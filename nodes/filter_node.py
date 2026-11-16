from services.pricing import final_price
from state import OverAllState


def unmatched_spec(item: dict, hard_specs: dict) -> str | None:
    """检查硬性规格。全部满足返回 None，否则返回第一个不满足的值。"""
    text = " ".join(str(v) for v in item["specs"].values())
    text = text.lower().replace(" ", "")

    for wanted in hard_specs.values():
        key = str(wanted).lower().replace(" ", "")
        if key not in text:
            return str(wanted)

    return None


async def filter_node(state: OverAllState) -> dict:
    req = state.get("requirement") or {}
    offers = state.get("offers") or []
    budget = req.get("budget")
    hard_specs = req.get("hard_specs") or {}

    kept = []
    dropped = []

    for item in offers:
        reason = ""

        if not item["stock"]:
            reason = "缺货"
        elif budget and final_price(item) > budget:
            reason = "超预算"
        else:
            bad = unmatched_spec(item, hard_specs) if item.get("specs") else None
            if bad:
                reason = f"不满足规格 {bad}"

        if reason:
            dropped.append({"name": item["name"], "reason": reason})
        else:
            kept.append(item)

    return {
        "offers": kept,
        "filter_report": {
            "input": len(offers),
            "kept": len(kept),
            "dropped": dropped,
        },
    }
