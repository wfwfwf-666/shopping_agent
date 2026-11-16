import os
import re

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv


load_dotenv()
mcp = FastMCP("shopping-tools")

# mcp tools
def clean(text: str) -> str:
    """清掉网页残留的 markdown / 图片占位。"""
    text = text or ""
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)   # ![alt](url)
    text = re.sub(r"Image \d+", "", text)          # Image 7
    text = re.sub(r"#+\s*", "", text)              # ## 标题
    text = re.sub(r"\[\.\.\.\]", "", text)         # [...]
    return re.sub(r"\s+", " ", text).strip()



@mcp.tool
async def web_search(query: str, max_results: int = 8):
    """
    搜索网页，返回标题、链接、摘要。用于查询商品评测、口碑与缺点。
    """
    async with httpx.AsyncClient(timeout=25) as c:
        r = await c.post(
            "https://api.tavily.com/search",
            json={"query": query, "max_results": max_results},
            headers={"Authorization": f"Bearer {os.getenv('TAVILY_API_KEY')}"},
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        lines = []
        for i,x in enumerate (results,1):
            lines.append(
                f"[{i}] {x.get('title', '')}\n{x.get('url', '')}\n{clean(x.get('content'))[:800]}"
            )
    return "\n\n".join(lines)






if __name__ == "__main__":
    mcp.run(show_banner=False)


