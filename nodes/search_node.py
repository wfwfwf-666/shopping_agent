from services.product_search import search_products
from state import OverAllState


async def search_node(state: OverAllState) -> dict:
    """联网检索候选商品。"""
    req = state.get("requirement") or {}
    offers = await search_products(req)
    return {"offers": offers}