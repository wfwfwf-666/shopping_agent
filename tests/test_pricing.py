"""价格计算：到手价、预算差、月供。"""

from services.pricing import compute, final_price

ITEM = {"price": 4499, "shipping": 0, "coupon": 189}


def test_final_price_basic():
    assert final_price(ITEM) == 4310


def test_final_price_includes_shipping():
    # 运费必须算进去，否则线上会出现「算出来的比实际便宜 12 块」
    item = {"price": 1000, "shipping": 20, "coupon": 50}
    assert final_price(item) == 970


def test_compute_with_budget():
    r = compute(ITEM, 5000)
    assert r["final"] == 4310
    assert r["diff"] == 690
    assert "结余" in r["budget_text"]
    assert r["monthly"] == round(4310 / 12, 2)


def test_compute_over_budget():
    r = compute(ITEM, 4000)
    assert r["diff"] == -310
    assert "超支" in r["budget_text"]


def test_compute_without_budget():
    r = compute(ITEM)
    assert r["diff"] is None
    assert r["budget_text"] == "未提供预算"
