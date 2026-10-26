import asyncio

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
load_dotenv()

def get_playwright_mcp_tool():
    # 把playwright MCP 临时下载到本地，并运行这个服务
    client = MultiServerMCPClient(
        {
            "playwright":{
                "transport": "stdio",  # stdio 表示本地使用，把playwright mcp下载到本地进行使用
                "command": "npx",
                "args": ["@playwright/mcp@latest"],
            }
        }
    )

    tools = asyncio.run(client.get_tools())
    return tools

# tools = get_playwright_mcp_tool()
# print(tools)

ds_llm = ChatDeepSeek(
    model = 'deepseek-v4-flash'
)

agent = create_agent(
    model=ds_llm,
    tools=get_playwright_mcp_tool(),
    system_prompt="You are a helpful assistant"
)

async def main():
    async for item in agent.astream(
        {
            "messages":[{'role':'user', 'content':'帮我打开 www.baidu.com，并输入 深圳今天天气如何？'}]
        }
    ):
        print(item, end='',flush=True)

if __name__ == '__main__':
    import _asyncio
    asyncio.run(main())
