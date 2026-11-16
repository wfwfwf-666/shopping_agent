"""联网找评测：reset 节点和流水线的评测步骤共用。"""

from services.web_search import search_web


async def search_reviews(product: str, max_results: int = 3) -> str:
    """搜一个商品的评测，失败时返回空字符串。"""
    return await search_web(f"{product} 评测 缺点", max_results=max_results)
