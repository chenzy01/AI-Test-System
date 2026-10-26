import fastmcp
from fastmcp import FastMCP

mcp = FastMCP("websearchSSE")
@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport='sse') # 指定协议