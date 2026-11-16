from typing import Literal

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

#格式化用户问的商品信息，提供给接下来的全部节点
class Requirement(BaseModel):
    budget: float | None = Field(
        None,
        description="预算上限，单位元。用户说五千/5k 要换算成 5000",
    )
    category: Literal["phone", "laptop", "headphone", "tablet", "other"] = "other"
    product: str | None = Field(
        None,
        description="用户明确提到的具体商品或型号，如 iPhone 16 Pro、小米15。没提到就留空",
    )
    hard_specs: dict[str, str] = Field(
        default_factory=dict,
        description="用户明确提出的硬性规格，键用参数名，如 {'显卡': 'RTX 5060', '存储': '512GB'}。"
                    "没提到的不要填。"
                    "键必须使用用户原话中的中文词（如显卡、存储），不要翻译成英文。",
    )
    soft_prefs: list[str] = Field(
        default_factory=list,
        description="主观偏好，如 拍照好、轻薄、续航久。"
                    "每条是一个简短短语（不超过 15 字），用中文自然语言描述，"
                    "不要写成 key: value 形式。例如「显卡最好是5060」「轻薄便携」。",
    )


#格式化商品价格
class PriceQuote(BaseModel):
    found: bool = Field(description="是否找到明确价格")
    product: str = Field(default="", description="识别出的商品型号")
    price: float | None = Field(default=None, description="价格，单位元")
    platform: str | None = Field(default=None, description="平台或店铺，如 京东、天猫")
    source: str | None = Field(default=None, description="来源链接")
    note: str = Field(default="", description="补充说明，如「仅供参考」")



# 主状态
class OverAllState(MessagesState):
    requirement: dict
    offers: list
    filter_report: dict
    decision: dict
    evaluations: dict
    budget_plan: dict


#检索信息
class ProductItem(BaseModel):
    name: str = Field(description="完整型号，如 华硕天选4 锐龙版 RTX4060")
    price: float = Field(description="价格，单位元")
    platform: str = Field(default="", description="平台或店铺")
    source: str = Field(default="", description="来源链接")
    specs: dict[str, str] = Field(default_factory=dict, description="材料里提到的规格")


class ProductList(BaseModel):
    products: list[ProductItem] = Field(default_factory=list)
