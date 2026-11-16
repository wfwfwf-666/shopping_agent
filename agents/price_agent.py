from langchain_core.messages import ToolMessage

from services.price_quote import lookup_price
from state import OverAllState


async def price_node(state: OverAllState) -> dict:
    last = state["messages"][-1]
    if not last.tool_calls:
        return {}

    req = state.get("requirement") or {}
    product = req.get("product")
    budget = req.get("budget")

    if not product:
        text = "你还没说想看哪款，能告诉我具体型号吗？"
    else:
        quote = await lookup_price(product)
        if quote.found and quote.price:
            text = f"{quote.product}：参考价约 ¥{quote.price:.0f}"
            if quote.platform:
                text += f"（{quote.platform}）"
            if budget:
                left = budget - quote.price
                if left >= 0:
                    text += f"；你的预算 ¥{budget:.0f}，大约还剩 ¥{left:.0f}"
                else:
                    text += f"；比预算 ¥{budget:.0f} 大约高 ¥{abs(left):.0f}"
            text += "。这是联网检索的参考价，不是实时报价，购买前请以商品页为准。"
            if quote.source:
                text += f" 来源：{quote.source}"
        else:
            text = f"没能查到「{product}」的明确价格。{quote.note}"

    return {
        "messages": [ToolMessage(content=text, tool_call_id=last.tool_calls[0]["id"])]
    }
