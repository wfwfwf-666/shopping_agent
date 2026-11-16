import asyncio

from services.pricing import compute
from services.review import search_reviews
from state import OverAllState

MAX_EVALUATE = 2  # 只评最便宜的前两款，控制耗时


async def evaluate_node(state: OverAllState) -> dict:
    offers = state.get("offers") or []
    if not offers:
        return {"evaluations": {}}

    top = sorted(offers, key=lambda item: compute(item)["final"])[:MAX_EVALUATE]

    texts = await asyncio.gather(*(search_reviews(item["name"]) for item in top))

    evaluations = {item["id"]: text for item, text in zip(top, texts)}
    return {"evaluations": evaluations}
