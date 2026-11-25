# AI 面试预测题 A · 50 题

> **出题依据**（三件套）：
> ① 新作品项目 czy-ai-system「kk AI 测试平台」（D:\PycharmProjects\czy-ai-system，Claude Code 开发的 LangGraph + MCP 用例生成平台）
> ② 简历 v8.1（AI 轨迹比对工具 / 多 Agent 测试流水线 / 4×N 质量左移矩阵 / RAG 线上问题应答）
> ③ 旧题库去重（Q03-Q06、Q08-Q12、Q16、A43-A50、Q39 等，同类型题标注复用并换角度）
>
> **标注说明**：锚点列标 📁 = 可从 czy-ai-system 真实代码找到答案（共 30 题，60%）；标 🧩 = 延伸/情景题（共 20 题，40%）。标 ⚡ = 旧题库已有答案可复用（换新角度）。
> 如与事实不符请纠正，我会基于纠正重新调整。

---

## 一、平台与架构（B01-B08）

| 编号 | 分类 | 问题原文 | 出题意图（考点） | 参考锚点 |
|---|---|---|---|---|
| B01 | 平台与架构 | 用 3 分钟介绍你的 kk AI 测试平台：它是做什么的、解决什么问题、核心能力有哪些？ | 考开场的项目表达力：能否讲清"痛点→方案→技术栈→现状"四段式；这是整场面试的定调题 | 📁 langgraph.json（两个图注册）、src/agents/test_case_agent.py、web/（Next.js 16 fork deep-agents-ui）、CLAUDE.md；与简历"多 Agent 测试流水线 1-2 天→2 小时"呼应 |
| B02 | 平台与架构 | 你为什么选 LangChain/LangGraph，而不是直接裸调模型 API，或者用 CrewAI？ | 考技术选型的判断力：知道裸调 API 缺什么（工具编排/状态/重试/流式生态），知道 LangGraph 与 CrewAI 的差异（显式图 vs 自动编排、可控性） | 📁 langchain_demo/（model_demo → tool_demo → agent_demo 的演进路径本身就是答案）、src/agents/test_case_agent.py；简历"通用 Agent 框架（LangGraph/CrewAI）了解" |
| B03 | 平台与架构 | LangGraph 的图（graph）和状态（state）机制是什么？在你的平台里是怎么体现的？ | 考是否真懂 LangGraph 而不是只会 create_agent 一把梭：节点/边/状态机、MessagesState、checkpoint 持久化的概念，以及"我目前是单 Agent 图，为什么够用、什么时候需要拆多节点" | 📁 langgraph.json 的 study_agent 与 test_case_agent 双图注册、src/agents/test_case_agent.py（create_agent 返回的图如何被 langgraph-sdk 消费）；简历"Coordinator 串行 4 子 Agent"可做对比 |
| B04 | 平台与架构 | 你的平台里模型为什么不直接内置解析 PDF 的能力，而要绕道 MCP + docling？——即：为什么用 MCP 而不是把工具写成普通函数做 Function Calling？ | 考对解耦的理解：工具进程隔离（解析服务崩溃不拖垮主进程）、传输层可换（stdio/SSE/HTTP）、工具可被任意 Agent 复用、生态标准化 | 📁 mcp/（HTTP_demo.py、stdio_demo.py、sse_demo_get_fastmcp.py 三种传输都实践过）、src/agents/test_case_agent.py 的 MultiServerMCPClient |
| B05 | 平台与架构 | 从用户在网页上传一份需求文档，到看到 Markdown 用例表格，数据完整流经了哪些环节？请把平台架构串讲一遍。 | 考端到端架构叙事能力：前端→LangGraph 服务→Agent→MCP→docling→LLM→流式回显；能不能讲清每一跳的协议（HTTP/SSE/SDK） | 📁 web/ 经 @langchain/langgraph-sdk 连 LangGraph 部署、src/agents/test_case_agent.py（sse transport, url=http://127.0.0.1:8000/sse）、start_server.py |
| B06 | 平台与架构 | 这个个人平台和你公司里做的"多 Agent 测试流水线"是什么关系？为什么不直接在公司项目里做这些？ | 考诚信与格局：个人项目是公司思路的独立开源化实现，用最新技术栈补齐了公司里做不了的探索；避免被质疑"个人项目是不是吹的" | 📁 整个仓库的技术选型（LangGraph 1.x / MCP / DeepSeek 均比公司项目更新）；⚡ 旧题库 Q09-Q12 多 Agent 流水线已有答案，本题换"关系对照"角度复用 |
| B07 | 平台与架构 | 平台现在做到什么程度了？后续还有什么规划？ | 考工程成熟度与 roadmap 意识：现状（单 Agent 用例生成 + Web UI + pytest）、规划（多 Agent 协作/评测闭环/用例管理对接）要能分层说 | 📁 现状：test_case_agent + study_agent + tests/；规划可结合简历"多 Agent 测试流水线"的 Coordinator 架构自然引出 |
| B08 | 平台与架构 | 如果要把这个平台在生产环境落地给团队用，你觉得还差哪些东西？ | 考风险自知：鉴权/多租户、成本与限流、评测与回归、可观测（trace/token 统计）、并发与稳定性——知道 demo 与生产的差距本身就是加分项 | 🧩 延伸题；可反向引用 src/middleware/pdf_parse_middleware 和 tests/ 作为"我已在补工程化"的证据 |

## 二、Agent 与 Prompt 工程（B09-B18）

| 编号 | 分类 | 问题原文 | 出题意图（考点） | 参考锚点 |
|---|---|---|---|---|
| B09 | Agent 与 Prompt | create_agent（create_react_agent）里的 ReAct 循环原理是什么？模型是怎么决定"再调一次工具"还是"输出最终答案"的？ | 考对 Agent 运行时本质的理解：Thought-Action-Observation 循环、工具结果回填 messages、无工具调用即终止；区分"会用"与"懂原理" | 📁 langchain_demo/agent_demo.py（从零手写过 agent 循环再到 create_agent 封装）、src/agents/test_case_agent.py |
| B10 | Agent 与 Prompt | 你的 system prompt 是怎么设计的？怎么把一套用例设计方法论"prompt 化"的？ | 考 prompt 工程实操：方法论分节（解析→拆需求点→三类场景→边界值规则→输出格式），结构化指令 vs 自然描述的取舍 | 📁 src/agents/test_case_agent.py 的 system_prompt 全文（三类场景覆盖、min/max/临界±1/空/非法、TC_001 递增、P0-P2、Markdown 表格）、czy_prompt/ 目录；⚡ 简历"Prompt 工程"经历呼应 |
| B11 | Agent 与 Prompt | 为什么要在 system prompt 里专门写"防臆造约束"（只依据文档、信息不足要声明假设）？不写会怎样？ | 考对 LLM 幻觉的实战认知：没有该约束时模型会脑补字段/规则；约束本质是给输出加"可追溯性"——这在测试领域是命门 | 📁 test_case_agent.py system_prompt 的防臆造段落；⚡ 简历"防幻觉三板斧"、旧题库 A44 幻觉量化可复用（本题换"prompt 层手段"角度） |
| B12 | Agent 与 Prompt | 工具调用失败或超时你怎么处理？为什么把 sse_read_timeout 设成 600 秒？这个值的工程含义是什么？ | 考异常处理的工程化：大 PDF 解析分钟级耗时 vs 默认超时过短的矛盾、超时后的重试/降级/用户提示策略 | 📁 src/agents/test_case_agent.py（MultiServerMCPClient, transport="sse", sse_read_timeout=600）；⚡ 旧题库 Q08 异常测试（含大模型输出异常）可复用（本题换"平台自身异常"角度） |
| B13 | Agent 与 Prompt | LangGraph 里 Agent 的记忆和状态是怎么管理的？MessagesState 里存了什么？多轮对话之间怎么传递？ | 考对状态机制的理解：messages 列表即短期记忆、thread_id 会话隔离、checkpoint 持久化的作用 | 📁 test_case_agent.py / study_agent 的状态流转、web/ 多轮对话实测；与简历"多 Agent 测试流水线的状态流转"对照 |
| B14 | Agent 与 Prompt | 用户连续上传好几份大文档后，上下文越滚越大，token 成本和效果都会出问题，你怎么处理上下文膨胀？ | 考长对话工程能力：消息裁剪/摘要压缩、文档内容结构化后只保留需求点而非全文、按 thread 管理生命周期 | 📁 system_prompt"先解析文档提取需求点再出用例"本身就是一种上下文压缩设计；🧩 延伸到 summarization/trim 策略 |
| B15 | Agent 与 Prompt | 你说"按需求点逐条出用例"，这个需求点拆解策略具体是怎么设计的？怎么保证拆得全、不重不漏？ | 考测试分析能力与 prompt 设计的接合：功能模块→子功能→可验证需求点三层拆解、MECE 意识、拆解粒度与用例数量的平衡 | 📁 test_case_agent.py system_prompt 的拆解指令、doc_loader_example/电商购物车需求文档.pdf（实测样例，可现场讲拆解效果） |
| B16 | Agent 与 Prompt | 用例生成的质量你是怎么持续优化的？从第一版到现在 prompt 改过几轮、改了什么？ | 考迭代方法论：bad case 驱动改 prompt、每轮改动对应什么质量问题（格式/覆盖率/臆造/粒度）、怎么验证改动有效 | 📁 czy_prompt/ 目录（prompt 演进痕迹）、src/agents/test_case_agent_1.py（旧版本对照）；⚡ 简历"用例准确率 50-60%→80%+"的优化叙事可复用 |
| B17 | Agent 与 Prompt | 你改了一版 system prompt，怎么保证新版本不会把原来好的地方改坏？——Prompt 的回归测试怎么做？ | 考 prompt 当代码的意识：固定输入集跑双版本 diff、关键断言（TC 编号连续/P0 存在/无臆造字段）、版本化留痕 | 📁 tests/ 现有 pytest 思路 + czy_prompt/ 版本留痕；⚡ 与 B41 呼应、旧题库 A46 评测集思路可复用 |
| B18 | Agent 与 Prompt | 如果文档解析失败、文档是空的、或者文档超长超出上下文，Agent 会发生什么？你设计过哪些边界情况的处理？ | 考测试工程师本色：给自己的平台做边界分析——正是 system prompt 里边界值规则（空/非法/临界）的"自我应用" | 📁 src/middleware/pdf_parse_middleware、tests/test_pdf_parse_middleware.py、test_file_parser.py；⚡ 旧题库 Q08 可复用（换"平台自身边界"角度） |

## 三、MCP 专题（B19-B24）

| 编号 | 分类 | 问题原文 | 出题意图（考点） | 参考锚点 |
|---|---|---|---|---|
| B19 | MCP | MCP 协议是什么？它解决了什么问题？没有 MCP 之前工具集成是什么状态？ | 考协议级理解：M×N 工具集成问题变 M+N、client/server/transport 三要素、资源/工具/提示词三类原语 | 📁 mcp/mcp_server.py + 三种传输 demo；🧩 结合行业现状（各家 Agent 框架工具生态割裂） |
| B20 | MCP | MCP 的三种传输方式 stdio、SSE、HTTP 各有什么区别？你为什么给 docling 选 SSE？ | 考传输层选型：stdio 适合本地子进程、SSE 适合服务化长连接、HTTP(streamable) 是新标准；docling 独立部署 + 长耗时解析需要服务化 | 📁 mcp/stdio_demo.py、HTTP_demo.py、sse_demo_get_fastmcp.py（三种都亲手写过）+ test_case_agent.py 的 SSE 选型 |
| B21 | MCP | 你自己开发过 MCP server 吗？开发一个 MCP server 的流程是什么？ | 考动手深度：用 FastMCP 定义工具、启动方式、客户端如何发现和调用工具；不只是消费别人的 server | 📁 mcp/mcp_server.py、mcp/sse_demo_get_fastmcp.py（FastMCP 实操）、start_server.py |
| B22 | MCP | docling 这个文档解析工具你是怎么集成的？解析 PDF 的效果怎么样，表格和图片能处理吗？ | 考集成细节：MultiServerMCPClient 配置、工具 schema 如何被模型感知、docling 对表格/图片的实际解析效果与局限 | 📁 src/agents/test_case_agent.py（MultiServerMCPClient + docling_mcp_tools）、doc_loader_example/pdf_loader.py + 电商购物车需求文档 PDF 实测 |
| B23 | MCP | MCP 工具有什么安全风险？比如工具滥用、prompt 注入污染工具描述、恶意 server，你怎么防？ | 考 AI 安全意识：工具描述注入（有毒 server 让模型泄露上下文）、过度授权、来源可信验证——2025 年面试高频新考点 | 🧩 延伸题；⚡ 旧题库 A45 Prompt 注入已有答案可复用（本题换"MCP 供应链"角度）+ 简历"大模型能力边界（幻觉/Prompt 注入）" |
| B24 | MCP | MCP 和 OpenAI Function Calling 是什么关系？有人说 MCP 就是个标准化的 Function Calling 接口，你同意吗？ | 考技术辨析：FC 是模型能力（模型决定调什么），MCP 是工具供给协议（工具怎么被发现/传输）；两者互补而非替代 | 📁 langchain_demo/tool_demo.py（裸 FC）vs src/agents/test_case_agent.py（MCP 路径）——同一仓库两条路线的对照就是最好的答案 |

## 四、LLM 技术基础（B25-B32）

| 编号 | 分类 | 问题原文 | 出题意图（考点） | 参考锚点 |
|---|---|---|---|---|
| B25 | LLM 基础 | 你为什么选 DeepSeek（deepseek-v4-flash）？和智谱 GLM、Claude 比，你的选型逻辑是什么？ | 考模型选型的成本-效果-场景三角：国产合规/价格/中文与结构化输出能力；重要的是"我对比过"而非"我听说" | 📁 src/core/llms.py（ChatDeepSeek 封装）+ langchain_demo/zhipu_demo.py（真接过智谱 GLM 做过对照）——"两家都调过"是硬证据 |
| B26 | LLM 基础 | temperature、top_p 这些采样参数，对你生成测试用例的质量有什么影响？你会怎么设？ | 考把 LLM 参数与测试场景挂钩：用例生成要稳定可复现→低温；归因/发散分析可适当高温；参数与确定性测试的矛盾 | 📁 src/core/llms.py 的模型参数配置；⚡ 简历 AI 轨迹比对工具"规则引擎+LLM 归因"中参数选择的实践可复用 |
| B27 | LLM 基础 | token 是怎么算的？上下文窗口有限，你的平台怎么管理长文档的 token 消耗？ | 考工程账感：中文 token 换算、文档→需求点的信息压缩、成本估算（一次生成大概多少 token 多少钱） | 📁 system_prompt 的"解析后只保留需求点"设计、doc_loader_example 的真实文档可现场估；🧩 与 B14 呼应但换"成本"角度 |
| B28 | LLM 基础 | 你的平台前端是流式看到输出的，SSE 流式输出的原理是什么？和 WebSocket 有什么区别？ | 考对"打字机效果"背后的理解：SSE 单向长连接/HTTP 协议/自动重连，vs WebSocket 双向；顺带讲 MCP 的 SSE 传输与模型输出流式的两层 SSE | 📁 web/ 的流式回显 + test_case_agent.py 的 sse transport（两层 SSE 可对比讲）+ mcp/sse_demo_get_fastmcp.py |
| B29 | LLM 基础 | 讲讲 RAG 的基本原理：embedding、向量检索、文档切片各是怎么回事？你在线上问题智能应答工具里是怎么用的？ | 考 RAG 全链路：切片策略（按语义/标题）、embedding 模型、top-k 检索、rerank；缺陷复盘蒸馏→检索→LLM 总结的落地细节 | ⚡ 旧题库 A47 RAG 测试、Q16 造数与 RAG 应答工具已有答案可复用；📁 平台侧可对照 docling 解析作为 RAG 的"入库前处理"环节 |
| B30 | LLM 基础 | 大模型幻觉是怎么产生的？从原理上讲讲，你有哪些系统性的缓解手段？ | 考原理层：训练目标与事实性的错位、采样随机性、知识截止；缓解：上下文约束（防臆造）/RAG 接事实/低温/校验 | ⚡ 旧题库 A44 幻觉量化已有答案可复用；📁 test_case_agent.py 防臆造约束 + 简历"防幻觉三板斧"是落地证据 |
| B31 | LLM 基础 | 什么问题该用 Prompt 工程解决，什么问题该上 RAG，什么问题必须微调？你的项目里怎么选的？ | 考三种技术手段的边界判断：知识注入→RAG、行为风格→prompt、领域深度+数据量足够→微调；成本递增序 | ⚡ 与旧题库 A43/A49 呼应但换"技术选型"角度；📁 平台现状 = 纯 prompt 方案的选择理由（方法论稳定、知识来自文档本身=RAG 化的文档解析） |
| B32 | LLM 基础 | 需求文档里的表格和图片，docling 解析得怎么样？多模态文档解析现在有哪些方案、各自局限？ | 考多模态认知：传统解析（表格结构还原）vs 视觉模型（图片理解）、版面分析、docling vs GPT-4V 类方案对比 | 📁 doc_loader_example/ 电商购物车 PDF（含表格实测）+ src/middleware/pdf_parse_middleware + tests/test_pdf_parse_middleware.py |

## 五、AI 测试专项深化（B33-B44）

| 编号 | 分类 | 问题原文 | 出题意图（考点） | 参考锚点 |
|---|---|---|---|---|
| B33 | AI 测试专项 | 你用 AI 生成测试用例，那谁来测试你的 AI 平台？——"AI 测 AI"的自举问题怎么破？ | 考元认知：确定性部分（解析/格式/编号）用传统断言、概率性部分（质量）用评测集+人工抽检；分层拆解不确定性 | 📁 tests/test_file_parser.py + test_pdf_parse_middleware.py（确定性层已覆盖）+ ⚡ 旧题库 A43 分层策略可复用 |
| B34 | AI 测试专项 | 用例生成质量的评测集怎么建？标注从哪来、标准怎么定、多少条够？ | 考评测体系建设：从公司用例库/评审记录抽标注样本、质量维度（覆盖率/可执行性/臆造率）、分层抽样 | ⚡ 旧题库 A46 评测集已有答案可复用（本题聚焦"用例生成"场景）；📁 doc_loader_example 的实测文档可做评测输入 |
| B35 | AI 测试专项 | 用 LLM-as-judge 来评 LLM 生成的用例，可行吗？怎么校准 judge 本身的不靠谱？ | 考前沿方法论：judge 与被评模型的偏置（自我偏好/位置偏置/长度偏置）、rubric 结构化、与人工标注的对齐率校准 | 🧩 延伸题；⚡ 与 A44 量化思路衔接，judge 校准可类比"测试 oracle 本身需要测试" |
| B36 | AI 测试专项 | docling 解析出来的结构对不对，你怎么验证？文档解析质量怎么评？ | 考对"非 LLM 组件"的测试思路：golden 文件比对、表格行列数断言、关键字段抽取召回——这是测试工程师的舒适区迁移到 AI 组件 | 📁 tests/test_pdf_parse_middleware.py（已有解析质量测试雏形）、doc_loader_example/pdf_loader.py + 样例 PDF |
| B37 | AI 测试专项 | 对一个 Agent 系统，端到端测试应该怎么做？怎么处理"每步都可能不确定"的情况？ | 考 Agent E2E 测试设计：关键路径断言（最终表格存在/TC 编号连续）而非逐步精确匹配、mock LLM 与真模型的分层测试金字塔 | 📁 test_case_agent 的端到端路径 + tests/ 现有分层；⚡ 旧题库 Q09-Q12 多 Agent 测试思路可复用（换"测 Agent 系统"角度） |
| B38 | AI 测试专项 | 你的平台要做性能测试，你会测哪些指标？TTFT、流式吞吐、并发分别怎么测？ | 考 LLM 应用的性能模型：TTFT（首 token 时间）比总时延更影响体验、token/s 吞吐、MCP 解析耗时的分离测量、并发下 API 限流 | ⚡ 旧题库 Q39 LLM API 压测已有答案可复用；📁 sse_read_timeout=600 + start_server.py 的部署链路可作测试对象锚点 |
| B39 | AI 测试专项 | 你平台的 pytest 测试目前覆盖了什么？为什么先测这些而不是别的？ | 考测试优先级判断：确定性组件先行（文件解析、中间件）、LLM 部分留给评测集——这是"知道什么该自动化断言"的判断力 | 📁 tests/test_file_parser.py、test_pdf_parse_middleware.py、conftest.py（直接可讲为什么这么分层） |
| B40 | AI 测试专项 | "AI 生成用例的可执行率"这个指标你会怎么定义和计算？分子分母各是什么？ | 考指标设计严谨性：生成总数 vs 可直接执行数（无需人工修改）、执行通过≠用例正确、口径陷阱 | ⚡ 简历"用例准确率 50-60%→80%+"的口径就是现成答案素材；🧩 延伸到执行层（用例转自动化脚本） |
| B41 | AI 测试专项 | prompt 也是一种"代码"，你怎么做 prompt 的版本管理和回归？ | 考工程化迁移能力：prompt 进版本库（czy_prompt/）、变更记录、双跑对比、坏例驱动回归集 | 📁 czy_prompt/ 目录 + src/agents/test_case_agent.py 与 test_case_agent_1.py 的版本对照（现成的演进证据） |
| B42 | AI 测试专项 | 算一笔账：AI 生成用例 vs 人工写用例，成本收益怎么算？什么场景 AI 划算、什么场景不划算？ | 考成本意识与商业 sense：token 成本+人力修正成本 vs 人力全写成本、文档质量是前提、简单 CRUD 划算/复杂业务逻辑仍需人 | ⚡ 简历"1-2 天→2 小时"的提效叙事可复用；🧩 延伸到团队推广的成本模型 |
| B43 | AI 测试专项 | AI 生成的测试用例有版权或合规问题吗？比如喂给模型的文档是公司的、生成的用例归谁？ | 考合规敏感度：训练数据与推理数据的区别、输入文档的保密要求（国产模型/私有化的理由）、生成物著作权争议 | 🧩 延伸题；可自然引出"为什么选 DeepSeek 而非海外模型"的合规理由（与 B25 呼应） |
| B44 | AI 测试专项 | 你的评测集如果长期拿来跑回归，模型会不会"对着评测集过拟合"？怎么防评测集泄漏？ | 考评测方法论深度：评测集版本轮换、holdout 集、bad case 污染（被修复的 case 反复进训练/优化视野）、盲测 | 🧩 延伸题；⚡ 与 A46 呼应但换"评测集自身的可信度"角度 |

## 六、情景与开放（B45-B50）

| 编号 | 分类 | 问题原文 | 出题意图（考点） | 参考锚点 |
|---|---|---|---|---|
| B45 | 情景与开放 | 假如入职后公司让你从 0 搭一个 AI 测试平台，你会怎么规划？前 3 个月做什么？ | 考落地路线图：先找高价值场景（文档→用例）做单点 MVP→评测闭环→流水线集成→平台化；czy-ai-system 就是一份现成答卷 | 📁 整个 czy-ai-system 即"从 0 到 1"实操证据；⚡ 旧题库 A49 AI 落地路线图可复用（本题换"平台建设"叙事） |
| B46 | 情景与开放 | 给你一个陌生的 Agent 系统，只有半天时间，你怎么快速摸底并给出测试方案？ | 考测试方法论的可迁移性：先跑通 happy path 看 trace→边界输入→工具失败注入→安全用例→输出质量抽检；半天的时间分配是关键 | 🧩 情景题；⚡ 旧题库 A43/B33/B37 的方法论在此综合运用；简历"多 Agent 流水线"测试经验背书 |
| B47 | 情景与开放 | AI 都能写用例了，测试工程师的核心价值还剩什么？ | 考职业认知深度：AI 生成的是"执行"，人负责"判断"——测试策略/风险优先级/质量标准定义/AI 输出的验收；反向证明"会用 AI 的测试工程师"更值钱 | ⚡ 旧题库 A50 转型最难、A43 本质区别可复用；🧩 结合自身"从传统测试→AI 测试主导者"的轨迹作答 |
| B48 | 情景与开放 | 你最近在学什么 AI 技术？为什么学它？ | 考学习真实性与热情：必须是真在学的（LangGraph 1.x/MCP/评测方法），能讲出"学了拿它干了什么"——czy-ai-system 就是学习产物 | 📁 整个仓库即"边学边做"证据（MCP 三传输 demo、LangChain demo 系列）；避免空谈"关注大模型发展" |
| B49 | 情景与开放 | 如果模型 API 明天涨价 10 倍，你的平台和业务怎么办？ | 考成本韧性设计：模型抽象层换供应商（llms.py 的封装价值）、缓存/降级/小模型路由、按价值分层调用 | 📁 src/core/llms.py（换模型只改一处）+ langchain_demo/zhipu_demo.py（证明多供应商切换能力）；🧩 延伸到成本监控 |
| B50 | 情景与开放 | 你怎么看 AI 测试未来 3 年的趋势？测试工程师要提前储备什么？ | 考行业判断力：Agent 评测标准化、评测工程师岗位兴起、AI 生成代码的测试责任边界、质量左移到 prompt/数据层 | 🧩 开放题；⚡ 旧题库 A49/A50 观点可复用，需换"3 年趋势"前瞻角度组织 |

---

## 八、AI 岗位共性题（B51-B68，2026-10-21 增补）

> **增补来源**：他人总结的 AI 岗位面试共性问题清单（36 个原始问题）。经与 B01-B50 逐条比对：**18 个与现有题高度重合，合并进现有条目**（映射见下表）；**18 个为全新角度，增补为 B51-B68**。

### 新增题目（18 题）

| 编号 | 分类 | 问题原文 | 出题意图 | 参考锚点 |
|---|---|---|---|---|
| B51 | 共性题 | 为什么这个需求适合用 Agent，而不是普通业务代码？ | 考"要不要 Agent 化"的业务判断力：非结构化文档理解+多步工具链+迭代推理是 Agent 的适用区；也要答得出"不适合 Agent 的场景"——展示双向判断 | 📁 test_case_agent（文档理解非结构化、docling 工具链、ReAct 迭代）；🧩 反例：纯计算/确定性流程用普通代码 |
| B52 | 共性题 | Agent 如何判断用户意图并选择不同处理流程？ | 考意图路由设计：单 Agent 场景的意图识别 vs 多流程场景的关键词路由 | 📁 czy 平台单 Agent 简单意图 + ⚡ 公司流水线 triggers/anti_triggers 意图路由（Q09 口径）——两个案例对照 |
| B53 | 共性题 | 执行到一半中断，状态如何保存和恢复？ | 考对 LangGraph checkpoint 的理解：thread_id 会话隔离、checkpointer 持久化、断点重放；中断恢复的三层设计 | 📁 langgraph 的 MessagesState/checkpoint 机制、web/ 多轮对话实测 |
| B54 | 共性题 | 如何避免 Agent 死循环或重复调用同一个工具？ | 考 ReAct 运行时的防护设计：轮数硬顶、重复检测、prompt 层终止条件——死循环是 ReAct 架构的天然风险 | 📁 create_agent 的 recursion_limit、test_case_agent 的迭代上限设计 |
| B55 | 共性题 | MCP 中设计了哪些 tools？每个 tool 的粒度怎么确定？ | 考工具设计能力：粒度=单一职责+参数可校验+返回可结构化；对照公司 5 Skill 粒度经验 | 📁 docling 单工具（单一职责反例佐证）+ ⚡ 公司流水线 5 个 Skill（一交付物一 Skill） |
| B56 | 共性题 | 为什么使用 RAG，而不是全文检索或直接把文档放进上下文？ | 考三种知识注入方式的辨析：语义检索 vs 关键词命中；token 成本/窗口限制/相关性稀释 | 🧩 三层对比框架 + ⚡ 线上问题应答工具（Q16/A47 口径） |
| B57 | 共性题 | 文档数量不多时，还有必要使用 RAG 吗？ | 考技术选型的诚实边界：小规模场景直接上下文+提示工程可能更优——敢说"不一定用"才是真懂 | 🧩 判断三条件框架（总量 token/更新频率/检索精度需求）；⚠ 线上应答工具当时文档规模需大哥核对 |
| B58 | 共性题 | RAG 没有召回正确内容时，怎么定位和优化？ | 考检索失败的分层定位实操：先分离检索层/生成层，再四步定位（query 理解→切片→embedding→阈值） | ⚡ A47 RAG 三层评测思路可复用（本题聚焦"定位实操"角度） |
| B59 | 共性题 | 会话记忆、执行状态、审计记录分别解决什么问题？ | 考三机制辨析：记忆=连续对话体验、状态=断点恢复、审计=事后追溯——各自丢失的后果不同 | 📁 MessagesState/thread_id/checkpoint + 🧩 审计层（呼应 B61） |
| B60 | 共性题 | AI 应用如何做全链路可观测？一次请求经过了哪些节点和工具怎么追踪？大模型调用失败从哪开始定位？ | 考可观测三支柱（logs/metrics/traces）：LangSmith/LangGraph trace、TTFT/成功率/成本指标、失败定位先分层 | 📁 langgraph dev 的 trace 能力 + 🧩 LangSmith 生态；⚡ B38 性能指标呼应 |
| B61 | 共性题 | 审计追踪具体审计哪些信息？ | 考审计要素设计：who/when/输入输出摘要/工具调用与参数/token 与成本——不可篡改留存 | 🧩 审计五要素框架 + ⚡ 公司工具调用留痕（anti_triggers 拦截记录）呼应 |
| B62 | 共性题 | 敏感信息如何识别和脱敏？ | 考 AI 场景的数据安全三层：输入层识别掩码、模型层合规、留存层日志脱敏 | ⚡ 压测线上数据脱敏经验（Q14 口径）+ 🧩 正则+NER 识别、国产模型合规理由（呼应 B25/B43） |
| B63 | 共性题 | 你平时如何使用 AI 完成一个完整需求？ | 考 AI 编程工作流的真实性：规格先行→骨架生成→迭代→测试验证→review；czy-ai-system 就是完整案例 | 📁 CLAUDE.md（项目规格与约定先行的证据）+ 整个仓库的 AI 协作开发痕迹 |
| B64 | 共性题 | AI 编程和传统编程有什么区别？ | 考认知深度：产物确定性（可推理 vs 需验证）、技能重心（语法→规格表达）、质量责任（测试更重）；测试视角有天然优势 | 🧩 三层对比；⚡ 以测试工程师身份答出"AI 代码更需要验证"的职业共振 |
| B65 | 共性题 | 如何保证 AI 生成代码的正确性和可维护性？ | 考 AI 代码质量体系：静态扫描+单测+review 抽样；引用 4×N 矩阵作为体系化答案 | 📁 tests/（单测先行证据）+ ⚡ A48 4×N 矩阵、AI 编码质量左移（简历项目四） |
| B66 | 共性题 | AI 生成了你不熟悉的技术方案，你会怎么验证？ | 考对 AI 输出的批判性验证——有真实案例：MCP/LangGraph 就是边学边做的新技术，验证路径可复述 | 📁 langchain_demo 系列（model→tool→agent 最小 demo 验证路径）+ tests/ 固化行为 |
| B67 | 共性题 | 你有没有沉淀自己的 rules、SPEC 或项目上下文？ | 考 AI 协作的工程化沉淀——三件套现成证据：CLAUDE.md、公司 5 个标准化 Skill、防踩坑模块 | 📁 CLAUDE.md 全文 + czy_prompt/ + ⚡ 公司 Skill 体系（Q11 口径） |
| B68 | 共性题 | AI 生成代码发生错误时，你怎么定位是提示词、上下文还是代码问题？ | 考三源定位法：先代码（最小复现）→再上下文（信息完整性）→后提示词（指令歧义）——控制变量验证 | 🧩 三源定位法 + 📁 tests/（最小复现的工具支撑） |

### 合并映射表（18 个原始问题 → 现有条目）

| 原始问题 | 归入 | 说明 |
|---|---|---|
| 整个 Agent 的运行流程是怎样的？ | B05 + B09 | 端到端链路（六跳）+ ReAct 循环原理，已覆盖 |
| 项目是单 Agent 还是多 Agent？为什么？ | B03 | "单 Agent 图为什么够用、什么时候拆多节点"已答 |
| MCP 在项目中解决了什么问题？ | B19 | M×N→M+N 协议价值已答 |
| 为什么使用 MCP，而不是直接调用 API、SDK 或 RPC？ | B04 + B24 | 进程隔离/传输可换/生态标准化 + MCP vs FC 辨析已答 |
| MCP 如何处理用户权限、租户隔离和数据安全？ | B23 + 增补段 | 安全风险已答；权限/租户角度见 B 部分增补段 |
| 工具调用失败后怎么重试和兜底？ | B12 + 增补段 | 三类失败场景已答；输出格式校验见增补段 |
| 大模型调用失败、超时或输出格式错误时怎么处理？ | B12 + 增补段 | 同上，增补段补输出格式错误处理 |
| RAG 的完整流程是什么？ | B29 | 切片/embedding/检索/生成全链路已答 |
| 如何判断模型生成的答案是否可信？ | B30 + 增补段 | 幻觉原理与缓解已答；可信判断三层见增补段 |
| 如何控制模型幻觉和错误输出？ | B30 | 已答（防臆造约束+三板斧） |
| 如何积累 bad case，并持续优化系统？ | B16 + 增补段 | prompt 迭代已答；bad case 库机制见增补段 |
| Prompt、知识库和模型发生变化后，怎么做回归测试？ | B17 + 增补段 | prompt 回归已答；知识库/模型变更维度见增补段 |
| 个人 AI 项目和真正的商业产品，主要差在哪里？ | B08 | 生产落地差距清单已答（鉴权/限流/评测/可观测/并发） |
| 你认为 AI 时代的开发者还需要具备哪些能力？ | B50 | 3 年趋势与能力储备已答 |
| 会话记忆怎么实现？ | B13 | MessagesState/thread_id 已答（B59 做三机制辨析补充） |
| 执行状态与 B53 重合 | B53 | 新题完整作答 |
| AI 编程正确性（部分） | B65 | 新题完整作答（引用 A48 4×N） |

---

## 附：题库使用说明

1. **分布**：平台与架构 8 + Agent/Prompt 10 + MCP 6 + LLM 基础 8 + AI 测试专项 12 + 情景开放 6 + **岗位共性增补 18 = 68 题**（B51-B68 为 2026-10-21 增补，源自他人总结的 36 个 AI 岗位共性问题，18 合并+18 新增）。
2. **60/40 达成**：📁 代码锚点题 30 道（B01-B05、B07、B09-B22、B24-B26、B28-B29、B32-B34、B36-B39、B41、B45、B48-B49），🧩 延伸情景题 20 道。
3. **复用提示**：⚡ 标注的题与旧题库答案重叠，备答时优先复用旧稿、按新角度补一段即可，不必重写。
4. **防臆造约束（自我应用）**：所有锚点均来自 czy-ai-system 实际目录结构与简历 v8.1；如项目后续有变动（如新增 Agent、更换模型），请告知，我会同步修订锚点。
