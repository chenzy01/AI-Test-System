
from langchain_core.tools import tool


def get_weather(city:str):
    """
    查询城市天气情况
    :param city: 城市名
    :return: 返回天气情况
    """
    return f'{city}是大晴天'

# weather_agent = create_agent(
#     model=ds_llm,
#     tools=[get_weather],  # 此处[get_weather]只是最简单的写法，正常情况有专门的工具调用
#     system_prompt='你是专业的天气播报员'
# )

@tool
def add_number(a:int, b:int) ->int:
    """两个整数想加"""
    return a + b

result = add_number.invoke({"a":1, "b":2})  # 当函数 add_number 加上装饰器@tool，函数必须加上注释说明，才能够正常运行
print(result)

print(add_number.name)
print(add_number.description)
print(add_number.args)

# 业务型写法
@tool(parse_docstring=True)  # parse_docstring 这个参数一定要写，表示工具会解析注释
def search_weather(city:str):
    # """
    # 查询城市天气情况
    # :param city: 城市名
    # :return: 返回天气情况
    # """
    # 采用上面写法，参数和return都 放在descrition中再传给大模型

    # 谷歌注释法
    """
    查询城市的天气情况
    Args:
        city(str): 城市
    Returns:
        str: 返回查询城市的天气情况
    """
    # 使用上面这种写法，会把参数和返回都分开传给大模型，上下文清晰
    return f'{city}是大晴天'
