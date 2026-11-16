import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel

from graph import DB_URI, build_graph

HERE = Path(__file__).resolve().parent

STEPS = {
    "parser": "解析需求",
    "supervisor_node": "主管判断",
    "transfer_to_price": "查询价格",
    "transfer_to_reset": "查询口碑",
    "transfer_to_pipeline": "开始挑选",
    "pipeline_filter": "硬性过滤",
    "pipeline_evaluate": "查询评测",
    "pipeline_finance": "财务核算",
    "pipeline_decide": "生成推荐",
}


class ChatIn(BaseModel):
    session_id: str
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时打开 PG 检查点，运行期间一直保持。"""
    if not DB_URI:
        raise RuntimeError("DB_URI 未配置，检查 .env")

    async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
        await saver.setup()
        app.state.graph = build_graph(checkpointer=saver)
        yield


app = FastAPI(title="购物决策助手", lifespan=lifespan)


def label_for(node: str, update: dict) -> str:
    """主管会进两次：第一次路由，第二次总结。"""
    if node == "supervisor_node":
        msgs = update.get("messages") or []
        if msgs and getattr(msgs[-1], "tool_calls", None):
            return "主管判断"
        return "总结回答"
    return STEPS.get(node, node)


def describe(node: str, update: dict) -> str:
    if node == "parser":
        req = update.get("requirement") or {}
        budget = req.get("budget")
        return f"预算 {budget if budget else '不限'}，品类 {req.get('category', 'other')}"
    if node == "transfer_to_pipeline":
        return f"找到 {len(update.get('offers') or [])} 款候选"
    if node == "pipeline_filter":
        r = update.get("filter_report") or {}
        return f"{r.get('input', 0)} 款筛到 {r.get('kept', 0)} 款"
    if node == "pipeline_evaluate":
        return f"拿到 {len(update.get('evaluations') or {})} 份评测"
    if node == "pipeline_finance":
        plan = update.get("budget_plan") or {}
        return f"核算 {len(plan.get('lines') or [])} 条报价"
    if node == "pipeline_decide":
        d = update.get("decision") or {}
        return "已生成推荐" if d.get("ok") else "没有符合条件的商品"
    if node in ("transfer_to_price", "transfer_to_reset"):
        return "已返回结果"
    return ""


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_chat(session_id: str, text: str):
    """同一个 session_id 就是同一个 thread_id，历史由 PG 自动恢复。"""
    config = {"configurable": {"thread_id": session_id}}
    answer = ""

    try:
        async for chunk in app.state.graph.astream(
            {"messages": [HumanMessage(content=text)]},
            config,
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                if not isinstance(update, dict):
                    continue

                msgs = update.get("messages")
                if msgs and isinstance(msgs[-1], AIMessage) and msgs[-1].content:
                    answer = msgs[-1].content

                yield sse({
                    "type": "step",
                    "label": label_for(node, update),
                    "detail": describe(node, update),
                })
    except Exception as e:
        yield sse({"type": "error", "content": f"{type(e).__name__}: {e}"})
        return

    yield sse({"type": "answer", "content": answer or "（没有生成回答）"})


@app.post("/api/chat")
async def chat(body: ChatIn):
    return StreamingResponse(
        stream_chat(body.session_id, body.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/history/{session_id}")
async def history(session_id: str):
    """从 PG 里读回该 thread 的完整历史。"""
    state = await app.state.graph.aget_state(
        {"configurable": {"thread_id": session_id}}
    )
    items = state.values.get("messages", []) if state and state.values else []

    out = []
    for m in items:
        # 工具结果是给模型看的，不展示给用户
        if isinstance(m, ToolMessage):
            continue
        content = getattr(m, "content", "")
        if not content:
            continue
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        out.append({"role": role, "content": content})
    return out


@app.get("/")
async def index():
    return FileResponse(HERE / "index.html")
