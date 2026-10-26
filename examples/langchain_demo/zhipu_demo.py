import os
from typing import Type

from cffi.recompiler import FieldExpr
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel, Field
from zai import ZhipuAiClient
from dotenv import load_dotenv
load_dotenv()


client = ZhipuAiClient(api_key=os.getenv("ZHIPU_API_KEY"))

@tool(parse_docstring=True)  # parse_docstring 这个参数一定要写，表示工具会解析注释
def search_weather(city:str) -> str:
    """查询城市的天气情况。

    Args:
        city: 查询城市的名称

    Returns:
        str: 返回查询城市的天气情况
    """
    # 使用上面这种写法，会把参数和返回都分开传给大模型，上下文清晰
    try:
        search_city = f'{city}今天天气如何'
        response = client.web_search.web_search(
            search_engine="search_pro",
            search_query= search_city
        )
        if response.search_result:
            return '\n\n'.join([ d.content for d in response.search_result])

    except Exception as e:
        return str(e)

# result = search_weather.invoke({"city":"深圳"})
# print(result)

# 接入大模型
# 定义大模型
ds_llm = ChatDeepSeek(
    model = 'deepseek-v4-flash'
)

# 定义智能体
agent1 = create_agent(
    model = ds_llm,
    tools = [search_weather],
    system_prompt="你是一个天气查询助手，使用 search_weather 工具查询天气"
)

result = agent1.invoke({
    'messages':[HumanMessage(content='深圳今天的天气如何？')]
})

print(result)

# -----------------------------------

class SearchArgs(BaseModel):
    city: str = Field(...,description="要查询城市的名称")
    # SearchArgs 因为继承了 BaseModel，所以会对该类下的变量进行强约束校验，city 字段一定要是字符串类型，Field 中的“...”表示必填


# 工具的另外一种写法，使用类（class），但要继承BaseModel
class Mytools(BaseModel):
    name:str = "weather search"
    description:str = "查询城市的经济情况"

    args_schema: Type[BaseModel] = SearchArgs

    def _run(self, city:str) -> str:  # _run方法是必须要重写的
        try:
            search_city = f'{city}今天的发展如何'
            response = client.web_search.web_search(
                search_engine="search_pro",
                search_query=search_city
            )
            if response.search_result:
                return '\n\n'.join([d.content for d in response.search_result])

        except Exception as e:
            return str(e)


search_economic = Mytools()

agent2 = create_agent(
    model = ds_llm,
    tools = [Mytools],
    system_prompt="你是一个天气查询助手，使用 Mytools 工具查询天气"
)
result2 = search_economic._run({'city': "深圳"})
print(result2)