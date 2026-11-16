from langchain_core.messages import ToolMessage

from services.pricing import compute
from state import OverAllState


def last_tool_call_id(messages):
    """找到主管那条带 tool_calls 的消息，取出 id。"""
    for msg in reversed(messages):
        if getattr(msg, "tool_calls", None):
            return msg.tool_calls[0]["id"]
    return None


async def decide_node(state: OverAllState) -> dict:
    req = state.get("requirement") or {}
    offers = state.get("offers") or []
    budget = req.get("budget")
    evaluations = state.get("evaluations") or {}

    if not offers:
        text = "没有符合全部条件的商品。可以试试放宽预算，或者去掉一些硬性要求。"
        result = {"decision": {"ok": False, "text": text}}
    else:
        ranked = sorted(offers, key=lambda item: compute(item)["final"])
        best = ranked[0]
        best_price = compute(best, budget)

        parts = [f"推荐 {best['name']}，到手 ¥{best_price['final']}"]
        if budget:
            parts.append(best_price["budget_text"])

        if len(ranked) > 1:
            second = ranked[1]
            second_price = compute(second)
            gap = second_price["final"] - best_price["final"]
            parts.append(f"备选 {second['name']}，到手 ¥{second_price['final']}（贵 ¥{gap}）")

        review_text = evaluations.get(best["id"])
        if review_text:
            snippet = " ".join(review_text.split())[:80]
            parts.append(f"口碑摘要：{snippet}")

        parts.append(f"共 {len(ranked)} 件符合条件")

        text = "；".join(parts)
        result = {
            "decision": {
                "ok": True,
                "recommend": best,
                "backup": ranked[1] if len(ranked) > 1 else None,
                "text": text,
            }
        }

    call_id = last_tool_call_id(state["messages"])
    if call_id:
        result["messages"] = [ToolMessage(content=text, tool_call_id=call_id)]

    return result
