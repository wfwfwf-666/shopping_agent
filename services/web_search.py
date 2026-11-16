"""通用联网搜索：评测、比价都从这里拿结果。"""

import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "shop": {
        "command": sys.executable,
        "args": [str(Path(__file__).resolve().parent.parent / "servers" / "tavily_mcp.py")],
        "transport": "stdio",
    }
})

# 缓存工具，避免每次调用都重启 MCP 子进程
_tools = None


async def get_tools():
    global _tools
    if _tools is None:
        _tools = await client.get_tools()
    return _tools


async def search_web(query: str, max_results: int = 4) -> str:
    """联网搜索，返回整理好的文本。失败返回空字符串，不抛异常。"""
    try:
        tools = await get_tools()
        search = next(t for t in tools if t.name == "web_search")
        res = await search.ainvoke({"query": query, "max_results": max_results})
        return res[0]["text"]
    except Exception as e:
        print(f"搜索失败: {type(e).__name__} - {e}")
        return ""
