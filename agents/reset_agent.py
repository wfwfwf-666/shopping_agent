from langchain_core.messages import ToolMessage

from services.review import search_reviews
from state import OverAllState


async def reset_node(state: OverAllState) -> dict:
    last = state["messages"][-1]
    if not last.tool_calls:
        return {}

    req = state.get("requirement") or {}
    product = req.get("product") or "这个商品"

    text = await search_reviews(product) or "暂时无法获取评测内容（搜索服务不可用）"

    return {
        "messages": [ToolMessage(content=text, tool_call_id=last.tool_calls[0]["id"])]
    }
