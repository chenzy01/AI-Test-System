import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
    {
        "playwright":{
            "transport": "sse",
            "url": "http://127.0.0.1:8000/sse",  # fastmcp 暴露出来的url
            "sse_read_timeout": 600
        }
    }
)

tools = asyncio.run(client.get_tools())
print(tools)