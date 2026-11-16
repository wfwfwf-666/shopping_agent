import asyncio
from servers.prompt import PARSER_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from servers.llm import get_parser_chain

from state import OverAllState

# 绑定结构化输出
model = get_parser_chain()


async def parser_node(state: OverAllState) -> dict:
    """用大模型精准提取预算和品类，并存入 State"""

    # 1. 从后往前找用户的原话（安全获取 HumanMessage）
    text = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            text = msg.content
            break

    if not text:
        return {"requirement": {}}

    # 2. 调用大模型进行结构化提取
    try:
        req = await model.ainvoke([
            SystemMessage(content=PARSER_PROMPT),
            HumanMessage(content=text)
        ])
        # 3. 把提取到的信息存入 State，供后面的节点使用
        return {"requirement": req.model_dump()}
    except Exception as e:
        print(f"提取需求失败: {e}")
        return {"requirement": {}}


