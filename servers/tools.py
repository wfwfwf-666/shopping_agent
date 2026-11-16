from langchain_core.tools import tool


@tool
def transfer_to_price() -> str:
    """当用户只问某个商品的价格、预算、分期、总花费时，转给查价 Agent。
    查价 Agent 会联网检索该商品的参考价。"""
    return "transferred"


@tool
def transfer_to_reset() -> str:
    """当用户只问某个商品的口碑、评测、缺点、值不值得买时，转给评测 Agent。"""
    return "transferred"


@tool
def transfer_to_pipeline() -> str:
    """当用户想让你帮忙挑选、推荐、在多个商品里做选择时，
    走完整决策流程（检索 → 硬性过滤 → 决策汇总）。"""
    return "transferred"
