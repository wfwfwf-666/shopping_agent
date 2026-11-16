"""模型工厂：目前统一用 DeepSeek。

以后想加 GLM / Qwen，改这里的 _deepseek 换成对应 client 即可，
上层节点不用动。
"""

import os
from functools import cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from state import PriceQuote, Requirement, ProductList

load_dotenv(override=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE")


def _deepseek(temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=SecretStr(DEEPSEEK_API_KEY or ""),
        base_url=DEEPSEEK_API_BASE,
        temperature=temperature,
        timeout=45,
        max_retries=1,
    )


@cache
def get_supervisor() -> ChatOpenAI:
    """主管：路由 + 总结。"""
    return _deepseek(0.2)


@cache
def get_parser_chain():
    """需求解析：话 -> Requirement。"""
    return _deepseek(0).with_structured_output(Requirement, method="function_calling")


@cache
def get_price_chain():
    """价格抽取：搜索结果 -> PriceQuote。"""
    return _deepseek(0).with_structured_output(PriceQuote, method="function_calling")

@cache
def get_product_chain():
    return _deepseek(0).with_structured_output(ProductList, method="function_calling")