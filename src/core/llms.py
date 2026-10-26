from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek

# 定义大模型的核心代码
ds_llm = ChatDeepSeek(
    model = 'deepseek-v4-flash'
    # temperature=0,
    # max_tokens=None,
    # timeout=0,
    # max_retries=2
)
