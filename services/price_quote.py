"""联网查价：从搜索结果里抽取价格。

不建数据库、不维护商品表 —— 每次按需搜索，抽出来的是「参考价」，
必须明确告知用户这不是实时报价。
"""

from langchain_core.messages import HumanMessage, SystemMessage

from servers.llm import get_price_chain
from servers.prompt import EXTRACT_PROMPT
from services.web_search import search_web
from state import PriceQuote


async def lookup_price(product: str) -> PriceQuote:
    text = await search_web(f"{product} 价格 多少钱 京东 淘宝 报价", max_results=4)
    if not text:
        return PriceQuote(found=False, product=product, note="搜索服务暂时不可用")

    try:
        quote = await get_price_chain().ainvoke([
            SystemMessage(content=EXTRACT_PROMPT),
            HumanMessage(content=f"商品：{product}\n\n检索结果：\n{text}"),
        ])
        quote.product = quote.product or product
        return quote
    except Exception as e:
        print(f"价格抽取失败: {type(e).__name__} - {e}")
        return PriceQuote(found=False, product=product, note="没能从搜索结果里提取出价格")
