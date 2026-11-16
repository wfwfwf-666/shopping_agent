import asyncio
import selectors
import sys

import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config("api.main:app", host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        # uvicorn 在 Windows 上默认用 ProactorEventLoop，psycopg 异步不支持
        asyncio.run(
            server.serve(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        server.run()
