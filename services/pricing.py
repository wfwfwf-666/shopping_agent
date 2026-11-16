"""价格计算：money 节点、filter 节点、决策流水线共用同一份公式。"""


def final_price(item: dict) -> float:
    """到手价 = 售价 + 运费 - 优惠。"""
    return item["price"] + item["shipping"] - item["coupon"]


def compute(item: dict, budget: float | None = None) -> dict:
    """算一个商品的到手价、预算差、月供。"""
    final = final_price(item)

    if budget:
        diff = budget - final
        if diff >= 0:
            budget_text = f"预算 ¥{budget}，结余 ¥{diff}"
        else:
            budget_text = f"预算 ¥{budget}，超支 ¥{abs(diff)}"
    else:
        diff = None
        budget_text = "未提供预算"

    return {
        "final": final,
        "diff": diff,
        "monthly": round(final / 12, 2),
        "budget_text": budget_text,
    }
