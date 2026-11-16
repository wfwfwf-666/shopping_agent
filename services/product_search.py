"""联网检索商品：搜索 + LLM 抽出结构化候选。"""

from langchain_core.messages import HumanMessage, SystemMessage

from servers.llm import get_product_chain
from servers.prompt import PRODUCT_EXTRACT_PROMPT
from services.web_search import search_web

CATEGORY_CN = {
    "phone": "手机",
    "laptop": "笔记本电脑",
    "headphone": "耳机",
    "tablet": "平板电脑",
    "other": "商品",
}


def _category_cn(requirement: dict) -> str:
    return CATEGORY_CN.get(requirement.get("category") or "other", "商品")


def build_query(requirement: dict) -> str:
    """搜索词：预算 + 品类 + 硬性规格 + 软性偏好。

    软性偏好很重要 —— 「头戴式」「游戏」这类词不进查询，
    搜出来就全是 TWS 耳塞。
    """
    parts = []
    budget = requirement.get("budget")
    if budget:
        parts.append(f"{int(budget)}元以内")
    parts.append(_category_cn(requirement))
    for value in (requirement.get("hard_specs") or {}).values():
        parts.append(str(value))
    for pref in (requirement.get("soft_prefs") or []):
        parts.append(str(pref))
    parts.append("推荐 价格")
    return " ".join(parts)


def build_desc(requirement: dict) -> str:
    """给抽取模型看的需求描述：刻意不含预算，避免被当成价格。"""
    parts = [_category_cn(requirement)]
    for value in (requirement.get("hard_specs") or {}).values():
        parts.append(str(value))
    for pref in (requirement.get("soft_prefs") or []):
        parts.append(str(pref))
    return " ".join(parts)


async def search_products(requirement: dict, max_results: int = 8) -> list[dict]:
    """联网搜商品，返回和 catalog 时期一致的 offers 结构。"""
    query = build_query(requirement)
    text = await search_web(query, max_results=max_results)
    if not text:
        return []

    budget = requirement.get("budget")
    header = f"商品需求：{build_desc(requirement)}"
    if budget:
        header += f"\n预算上限：{int(budget)} 元（这是预算，不是商品价格）"

    try:
        result = await get_product_chain().ainvoke([
            SystemMessage(content=PRODUCT_EXTRACT_PROMPT),
            HumanMessage(content=f"{header}\n\n检索材料：\n{text}"),
        ])
    except Exception as e:
        print(f"商品抽取失败: {type(e).__name__} - {e}")
        return []

    offers = []
    for i, item in enumerate(result.products[:max_results], 1):
        if not item.price:
            continue
        offers.append({
            "id": f"web-{i}",
            "name": item.name,
            "price": float(item.price),
            "shipping": 0,
            "coupon": 0,
            "stock": True,
            "specs": item.specs or {},
            "platform": item.platform,
            "source": item.source,
        })
    return offers
