from unittest import result

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_deepseek import ChatDeepSeek
load_dotenv()

# 定义大模型
ds_llm = ChatDeepSeek(
    model = 'deepseek-v4-flash'
    # temperature=0,
    # max_tokens=None,
    # timeout=0,
    # max_retries=2
)
# 定义智能体
study_agent = create_agent(
    model = ds_llm,
    tools = [],
    system_prompt="You are a helpful assistant"
)

result1 = study_agent.invoke({
    'messages':[HumanMessage(content='深圳今天的天气如何？')]
})
# result1 = agent.invoke({
#     "input": "深圳今天的天气如何？"
# })

print(result1)