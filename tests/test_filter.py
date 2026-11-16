"""硬性过滤：缺货、超预算、规格不满足。"""

import asyncio

from nodes.filter_node import filter_node, unmatched_spec


def make_item(name="测试机", stock=True, price=1000, shipping=0, coupon=0, specs=None):
    return {
        "name": name,
        "stock": stock,
        "price": price,
        "shipping": shipping,
        "coupon": coupon,
        "specs": specs or {},
    }


def run_filter(offers, requirement):
    return asyncio.run(filter_node({"offers": offers, "requirement": requirement}))


def test_drop_out_of_stock():
    offers = [make_item("缺货的", stock=False), make_item("有货的")]
    out = run_filter(offers, {})
    assert [i["name"] for i in out["offers"]] == ["有货的"]
    assert out["filter_report"]["dropped"][0]["reason"] == "缺货"


def test_drop_over_budget():
    offers = [make_item("贵", price=9000), make_item("便宜", price=3000)]
    out = run_filter(offers, {"budget": 5000})
    assert [i["name"] for i in out["offers"]] == ["便宜"]
    assert out["filter_report"]["dropped"][0]["reason"] == "超预算"


def test_budget_uses_final_price_not_list_price():
    # 9000 的机器有 1500 优惠券，到手 7500，预算 8000 应该通过
    offers = [make_item("有券", price=9000, coupon=1500)]
    out = run_filter(offers, {"budget": 8000})
    assert out["filter_report"]["kept"] == 1


def test_drop_missing_spec():
    offers = [make_item("256G", specs={"存储": "256GB"})]
    out = run_filter(offers, {"hard_specs": {"存储": "512GB"}})
    assert out["filter_report"]["kept"] == 0
    assert "512GB" in out["filter_report"]["dropped"][0]["reason"]


def test_spec_match_ignores_case_and_space():
    assert unmatched_spec({"specs": {"显卡": "RTX4060"}}, {"显卡": "rtx 4060"}) is None
    assert unmatched_spec({"specs": {"显卡": "集成显卡"}}, {"显卡": "4060"}) == "4060"


def test_no_budget_means_no_price_filter():
    offers = [make_item("很贵", price=99999)]
    out = run_filter(offers, {})
    assert out["filter_report"]["kept"] == 1


def test_empty_offers():
    out = run_filter([], {"budget": 5000})
    assert out["offers"] == []
    assert out["filter_report"]["input"] == 0
