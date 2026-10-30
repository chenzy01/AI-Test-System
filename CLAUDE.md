# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

「CZY AI测试平台」—— 基于 LangChain/LangGraph 的 AI 智能体系统，核心能力是让智能体解析需求/设计/接口文档，自动生成测试用例。

- 后端：Python 3.12+，LangChain 1.x + LangGraph + DeepSeek（`deepseek-v4-flash`，多模态），用 uv 管理依赖（`pyproject.toml` / `uv.lock`）。
- 文档解析：自定义 LangChain 中间件 `PdfParseMiddleware` 在模型调用前解析用户上传的文件（PDF/图片/文本/CSV/XLSX），走 PyMuPDF4LLM + 千问多模态模型，不再依赖 docling MCP。
- 测试技能：`src/skills/` 下 5 个企业级测试技能（需求分析→测试点提取→用例生成→用例评审→报告生成），按 Agent Skills 官方规范组织。
- 前端：`web/` 是 Next.js 16 + React 19 的聊天 UI，从 langchain-ai/deep-agents-ui fork 而来（"Deep Agents UI"），通过 `@langchain/langgraph-sdk` 连接 LangGraph 部署。

## 常用命令

### 后端（Python）

依赖用 uv + 项目根目录的 `.venv`。安装/同步依赖：

```bash
uv sync
```

启动 LangGraph API 服务器（端口 2026，读取 `langgraph.json` 注册图、加载 `.env`）：

```bash
uv run start_server.py
# 或先激活 .venv 后 python start_server.py
```

LangGraph 官方开发模式（等价方式，默认端口 2024）：

```bash
langgraph dev
```

跑测试（pytest，根目录 `conftest.py` 会把项目根目录加进 `sys.path`）：

```bash
uv run pytest
# 或激活 .venv 后 pytest
```

### 前端（web/）

包管理器固定为 yarn 1.x（`package.json` 中 `packageManager: yarn@1.22.22`）：

```bash
cd web
yarn install
yarn dev      # next dev --turbopack，默认 http://localhost:3000
yarn lint     # eslint
yarn build    # next build
```

前端启动后在 UI「设置」里填入 LangGraph 部署地址（deploymentUrl，如 `http://localhost:2026`）和 assistantId（即 `langgraph.json` 里的图名，如 `test_case_agent_1`），配置保存在 localStorage。

## 架构

### 图（Agent）注册

`langgraph.json` 是图的唯一注册入口，当前定义 3 个可被前端调用的图，并指定 `"env": ".env"`：

- `study_agent` → `./examples/langchain_demo/agent_demo.py:study_agent`（学习 demo）
- `test_case_agent_1` → `./src/agents/test_case_agent_1.py:test_case_agent`（核心：测试用例生成，含文件解析中间件）
- `deep_agent` → `./examples/deepagents_demo/deep_demo.py:agent`（Deep Agents 多智能体 demo，挂载 skills）

新增一个可对外服务的智能体 = 在对应 `.py` 里定义一个 `create_agent(...)` 对象，再在 `langgraph.json` 的 `graphs` 加一行 `"名字": {"path": "./xxx.py:对象名"}`。

### 后端目录

- `src/core/llms.py`：统一大模型定义 `ds_llm = ChatDeepSeek(model='deepseek-v4-flash')`，所有 agent 从这里 import，改模型只动这一处。
- `src/agents/test_case_agent_1.py`：当前对外服务的测试用例生成智能体。`tools=[]`、`middleware=[check_message, PdfParseMiddleware()]`——文件解析走中间件，docling MCP 调用已注释（旧方案）。内置 system_prompt 输出 Markdown 表格用例。
- `src/agents/test_case_agent.py`：旧版，通过 MCP 客户端（SSE `http://127.0.0.1:8000/sse`）调用 docling 工具解析文档。已不在 `langgraph.json` 注册（遗留；运行需先启 docling MCP 服务监听 8000 端口）。
- `src/middleware/pdf_parse_middleware.py`：`PdfParseMiddleware`（继承 `AgentMiddleware`）。模型调用前遍历消息里的 `type=='file'` 块 → 统一转 base64 → 按 MIME 分发到解析入口 → 追加进 SystemMessage → 剥离原始 base64（防 token 爆炸）→ 按消息 id / base64 sha1 缓存 → 解析失败降级不崩溃。同步 `wrap_model_call` + 异步 `awrap_model_call` 双实现。
- `src/utils/pdf_parser.py`：`parse_pdf_base64(base64) -> str`，用 PyMuPDF4LLM（`mode='single'`、`use_ocr=False`）+ 千问多模态 `LLMImageBlobParser` 解析 PDF（含图片/表格），返回 Markdown 全文。
- `src/utils/file_parser.py`：`parse_image_base64` / `parse_text_base64` / `parse_csv_base64` / `parse_xlsx_base64`，补齐 PDF 之外的文件类型，供中间件按 MIME 分发。解析契约统一：入参 base64 → 返回 Markdown。
- `src/skills/`：5 个企业级测试技能（详见下节）。

### 测试技能（src/skills/）

按 Agent Skills 官方规范（agentskills.io / anthropics/skills）组织的 5 个技能，链路串联、ID 全链路可追溯：`RA-`（需求）→ `TP-`（测试点）→ `TC-<模块简称>-`（用例）。

每个技能目录结构：`SKILL.md`（YAML frontmatter + 七章骨架：角色定义 / 输入契约 / 输出契约 / 工作流程 / 质量门禁 8 条 / 参考文档索引 / 输出约定）+ `references/`（≥3 个按需加载的参考文档）+ `evals/evals.json`（3 条真实感测试 prompt）。

| 目录 / name | 职责 | 输入 → 输出 |
|---|---|---|
| `requirement-analysis` | 需求分析 | 需求文档文本 → 需求清单（RA-xxx，含类型/业务规则/约束/验收标准/优先级/疑点假设） |
| `test-point-extraction` | 测试点提取 | 需求清单 → 测试点清单（TP-xxx，含关联 RA-ID/测试关注点/测试类型/建议方法/优先级） |
| `testcase-generation` | 测试用例生成 | 测试点清单 → 测试用例集（TC-模块-xxx，八大字段） |
| `testcase-review` | 测试用例评审 | 测试用例集 → 评审报告（七维度问题，按必须改/建议改/可选分级） |
| `test-report-generation` | 测试报告生成 | 执行结果 + 缺陷 → 测试报告（六大板块 + 度量指标） |

⚠️ 技能矩阵消费的是「解析后的文本」，不关心文件从哪来（文档解析由中间件层统一处理）。当前这些技能尚未接入任何 agent，接入属后续任务。

### 文档解析数据流

前端上传文件（base64，`type:"file"` / `type:"image"` 块）→ `PdfParseMiddleware`（`wrap_model_call`）提取文件块 → 按 MIME 分发到 `src/utils/pdf_parser.py` 或 `src/utils/file_parser.py` 的对应入口 → Markdown 全文 → 追加进 SystemMessage → 交给 DeepSeek。同一文件在多轮循环里只解析一次（缓存）。

### 前端目录（web/）

- 单页应用：`src/app/page.tsx` 是入口，对话流核心状态在 `src/app/hooks/useChat.ts`（用 `@langchain/langgraph-sdk/react` 的 `useStream` 驱动）。
- `src/providers/ClientProvider.tsx` 创建 langgraph-sdk 的 `Client`；`ChatProvider.tsx` 包装 `useChat`。
- `src/lib/config.ts`：管理 localStorage 里的连接配置（key `deep-agent-config`，含 deploymentUrl / assistantId / langsmithApiKey）。
- `src/lib/multimodal-utils.ts`：多模态文件块格式 + `Base64FileBlock` 类型 + `isBase64ContentBlock` 守卫（前端把文件统一成 Python 侧可识别的标准块：`source_type:"base64"` + `mime_type`）。
- `src/app/hooks/useFileUpload.ts`：文件上传状态管理；`src/app/components/MultimodalPreview.tsx`、`ContentBlocksPreview.tsx`、`FileViewDialog.tsx`：文件预览 / 内容块展示。
- `src/app/components/` 其余是业务组件（聊天、线程列表、工具调用展示、中断处理），`src/components/ui/` 是 shadcn 风格基础 UI 组件。

### 数据流

前端（Next.js）→ langgraph-sdk → LangGraph API 服务器（`start_server.py`:2026）→ 注册的图（如 `test_case_agent_1`）→ `PdfParseMiddleware` 解析上传文档 → DeepSeek 大模型生成测试用例。

## 其它目录与说明

- `examples/mcp/`：MCP 客户端/服务端三种传输方式（stdio/sse/http）示例；`mcp_server.py` 是 FastMCP SSE 服务。⚠️ `HTTP_demo.py` 硬编码了一个 Tavily API key（已失效），已加入 `.gitignore` 不提交。
- `examples/doc_loader_example/`、`examples/langchain_demo/`：PDF 加载（PyMuPDF4LLM + 千问多模态解析图片）与 LangChain 基础用法示例；目录下的 `.pdf` 是测试用需求文档样本。
- `examples/langchain/doc_embedding/`：向量计算与检索示例。`dashscope_embedding_demo.py` 用阿里 DashScope `text-embedding-v4` 做向量化 + `RedisVectorStore`（`langchain_redis`）做相似度检索（`similarity_search_with_score`，`1-score` 得相似度）；`ollama_embedding_demo.py` 用本地 Ollama `nomic-embed-text` 做向量化（`embed_query` / `embed_documents`，768 维）。
- `examples/deepagents_demo/`：`deep_demo.py` 用 `create_deep_agent` + `FilesystemBackend`（`virtual_mode=True`）挂载 `skills/` 目录；其 `skills/` 是 5 个**旧版**技能（用 `templates/` 目录，命名与 `src/skills` 新版也不同，勿混用）。
- `examples/czy_prompt/`：开发中间件 / PDF 解析器时用的提示词（如 `PDF_middleware.md`），沉淀开发需求。
- `tests/`：`test_file_parser.py`（解析入口，离线无网络）、`test_pdf_parse_middleware.py`（中间件，覆盖正常 / 缓存 / 异常降级 / 剥离 base64 / 多类型 / 字段兼容等 10 个用例）。
- `docs/`：AI 面试预测题笔记（个人学习资料，与平台代码无关）。
- `README.md`：开发笔记（学习过程记录，非标准项目 README）；`main.py`：PyCharm 生成样板（`print_hi`），非项目代码。

## 环境与注意事项

- `.env`（根目录）需要的 key：`DEEPSEEK_API_KEY`、`ZHIPU_API_KEY`、`DASHSCOPE_API_KEY`、`DOCLING_MCP_CONVERSION_MODE`。其中 `DASHSCOPE_API_KEY` 现用于 PDF/图片多模态解析（`qwen3.8-omni-flash`，见 `src/utils/pdf_parser.py`）。`start_server.py` 强制 `PYTHONUTF8=1` 规避 Windows GBK 解码问题。
- 导入约定：统一用绝对导入 `from src.core.llms import ...`（依赖 `langgraph.json` 的 `"dependencies": ["."]` 把根目录加进 `sys.path`）。⚠️ 例外：`src/agents/test_case_agent_1.py` 写的是 `from middleware.pdf_parse_middleware import ...`（依赖 `start_server.py` 把 `src/` 加进 path），与其它模块不一致，建议统一为 `from src...`。
- 直接 `python src/xxx.py` 单独运行会 import 失败，需从根目录跑或经 `start_server.py`。
- `.gitignore`（根目录）已存在：忽略 `.env*`、`examples/mcp/HTTP_demo.py`、`.venv/`、`__pycache__/`、`.pytest_cache/`、`.langgraph_api/`、`.idea/`、`node_modules/`、`.next/`。
- `.langgraph_api/`、`.venv/`、`__pycache__/` 等是运行时产物，勿纳入改动范围。
