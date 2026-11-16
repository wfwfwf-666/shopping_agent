from services.pricing import compute
from state import OverAllState


async def finance_node(state: OverAllState) -> dict:
    req = state.get("requirement") or {}
    budget = req.get("budget")
    offers = state.get("offers") or []

    lines = []
    for item in offers:
        p = compute(item, budget)
        lines.append({
            "id": item["id"],
            "name": item["name"],
            "final": p["final"],
            "diff": p["diff"],
            "monthly": p["monthly"],
        })

    return {"budget_plan": {"budget": budget, "lines": lines}}
