from typing import Literal
from langchain_core.messages import SystemMessage
from servers.prompt import SUPERVISOR_PROMPT
from langgraph.constants import END
from langgraph.types import Command
from servers.llm import get_supervisor
from servers.tools import transfer_to_price, transfer_to_pipeline, transfer_to_reset
from state import OverAllState

model = get_supervisor()

model_with_tools = model.bind_tools(
    [transfer_to_price, transfer_to_reset, transfer_to_pipeline],
    parallel_tool_calls=False,  # 一次只选一个工具
)


async def supervisor_node(state: OverAllState) -> Command[Literal[
    "transfer_to_price",
    "transfer_to_reset",
    "transfer_to_pipeline",
    "__end__",
]]:
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    res = await model_with_tools.ainvoke(messages)

    if res.tool_calls:
        goto = res.tool_calls[0]["name"]
    else:
        goto = END

    return Command(goto=goto, update={"messages": [res]})
