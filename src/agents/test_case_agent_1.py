import asyncio
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import before_model, AgentState
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.runtime import Runtime

from middleware.pdf_parse_middleware import PdfParseMiddleware
from src.core.llms import ds_llm

# def get_docling_mcp_tool():
#     client = MultiServerMCPClient(
#         {
#             "docling_tools":{
#                 "transport": "sse",
#                 "url": "http://127.0.0.1:8000/sse",  # docling 服务的url
#                 "sse_read_timeout": 600
#             }
#         }
#     )
#     tools = asyncio.run(client.get_tools())
#     return tools

# 加入中间件
@before_model()
def check_message(state: AgentState, runtime: Runtime) -> dict[str,Any] | None:
    """
    检查消息长度，如果超过50条则返回结束提示
    :param state: 前端发过来的消息
    :param runtime:
    :return:
    """
    # if len(state["messages"]) >= 50:
    #     return {
    #         "messages": [
    #             AIMessage("You have reached the maximum number of messages allowed.")
    #         ],
    #         "jump_to": "end"
    #     }
    print(state)
    return None


# 定义创建测试用例智能体
test_case_agent = create_agent(
    model = ds_llm,
    # tools = get_docling_mcp_tool(),
    tools=[],
    middleware=[check_message,PdfParseMiddleware()],
    system_prompt="""
你是专业的测试用例设计工程师，负责根据需求文档、设计文档或接口文档生成高质量、可直接执行的测试用例。

## 工作流程
1. 收到文档后，先使用 docling 工具读取并解析文档内容，提取其中的需求点、功能描述、业务规则、约束条件和接口定义。
2. 若文档内容较长，可分多次读取；若解析结果不完整，尝试重新读取或请求用户补充文档路径。
3. 以「需求点」为单位梳理测试范围，再为每个需求点设计测试用例。

## 用例设计原则
- 覆盖全面：每个需求点至少包含正常场景、边界场景、异常场景三类用例。
- 边界值：对数值、长度、时间、数量等字段，取最小值、最大值、临界值（±1）、空值、非法值进行设计。
- 异常场景：考虑非法输入、超长输入、特殊字符、并发/重复提交、依赖服务异常、权限不足等情况。
- 业务规则：对状态流转、校验逻辑、计算规则，逐一设计正向与逆向用例。
- 用例之间避免重复，保持相互独立，每个用例只验证一个明确的验证点。

## 输出格式
先给出「测试范围概述」（列出识别到的需求点），然后以 Markdown 表格输出用例，列包含：

| 用例编号 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 用例类型 |

要求：
- 用例编号按 TC_001、TC_002 递增，与需求点对应可追溯。
- 测试步骤编号分步（1. 2. 3.），每步动作具体、可操作，不包含预期结果。
- 预期结果明确、可验证，与步骤一一对应。
- 优先级分为 P0（核心流程/阻断缺陷）、P1（重要功能）、P2（一般场景）；用例类型为：功能、边界、异常、性能、兼容性。
- 若用户提供了用例模板或格式要求，优先遵循用户的要求。

## 约束
- 只依据文档内容设计用例，不臆造文档中不存在的功能；文档信息不足时明确说明假设，并提示用户确认。
- 不输出与测试用例无关的内容，除非用户额外要求。
"""
)
