import asyncio
import os
import sys
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from langgraph.constants import START
from langgraph.graph import StateGraph
from nodes.decide_node import decide_node
from nodes.evaluate_node import evaluate_node
from nodes.finance_node import finance_node
from nodes.filter_node import filter_node
from agents.price_agent import price_node
from nodes.parser_node import parser_node
from agents.reset_agent import reset_node
from nodes.search_node import search_node
from agents.supervisor_agent import supervisor_node
from state import OverAllState
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DB_URI")


builder = StateGraph(state_schema=OverAllState)

builder.add_node("parser", parser_node)
builder.add_node("supervisor_node", supervisor_node)
builder.add_node("transfer_to_price", price_node)
builder.add_node("transfer_to_reset", reset_node)
builder.add_node("transfer_to_pipeline", search_node)
builder.add_node("pipeline_filter", filter_node)
builder.add_node("pipeline_evaluate", evaluate_node)
builder.add_node("pipeline_finance", finance_node)
builder.add_node("pipeline_decide", decide_node)

builder.add_edge(START, "parser")
builder.add_edge("parser", "supervisor_node")
builder.add_edge("transfer_to_price", "supervisor_node")
builder.add_edge("transfer_to_reset", "supervisor_node")
builder.add_edge("transfer_to_pipeline", "pipeline_filter")
builder.add_edge("pipeline_filter", "pipeline_evaluate")
builder.add_edge("pipeline_evaluate", "pipeline_finance")
builder.add_edge("pipeline_finance", "pipeline_decide")
builder.add_edge("pipeline_decide", "supervisor_node")

def build_graph(checkpointer=None):
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()


async def main():
    # 注意：PostgresSaver 的上下文管理器内部也要用异步方式
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
        await saver.setup()
        g = builder.compile(checkpointer=saver)
        config = {
            "configurable": {
                "thread_id": "1"
            }
        }

        # 关键修改：使用 await g.ainvoke() 代替 g.invoke()
        r1 = await g.ainvoke({"messages": [HumanMessage(content="华硕天选4 多少钱")]}, config)
        r2 = await g.ainvoke({"messages": [HumanMessage(content="那它值得买吗")]}, config)


        for msg in r1["messages"]:
            msg.pretty_print()
        for msg in r2["messages"]:
            msg.pretty_print()


if __name__ == "__main__":
    # psycopg 的异步模式不支持 Windows 默认的 ProactorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

