# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

「CZY AI 测试平台」—— 基于 LangChain/LangGraph 的 AI 智能体系统，核心能力是让智能体通过 MCP 工具解析需求/设计/接口文档，自动生成测试用例。

- 后端：Python 3.12+，LangChain 1.x + LangGraph + DeepSeek，用 uv 管理依赖（`pyproject.toml` / `uv.lock`）。
- 前端：`web/` 是 Next.js 16 + React 19 的聊天 UI，从 langchain-ai/deep-agents-ui fork 而来（"Deep Agents UI"），通过 `@langchain/langgraph-sdk` 连接 LangGraph 部署。

## 常用命令

### 后端（Python）

依赖用 uv + 项目根目录的 `.venv`。安装/同步依赖：

```bash
uv sync
```

启动 LangGraph API 服务器（端口 2026，会读取 `langgraph.json` 注册图、加载 `.env`）：

```bash
uv run start_server.py
# 或先激活 .venv 后 python start_server.py
```

LangGraph 官方开发模式（等价方式，默认端口 2024）：

```bash
langgraph dev
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

前端启动后在 UI「设置」里填入 LangGraph 部署地址（deploymentUrl，如 `http://localhost:2026`）和 assistantId（即 `langgraph.json` 里的图名，如 `test_case_agent`），配置保存在 localStorage。

## 架构

### 图（Agent）注册

`langgraph.json` 是图的唯一注册入口，当前定义了两个可被前端调用的图：

- `study_agent` → `examples/langchain_demo/agent_demo.py:study_agent`（学习 demo）
- `test_case_agent` → `src/agents/test_case_agent.py:test_case_agent`（核心：测试用例生成）

新增一个可对外服务的智能体 = 在对应 `.py` 里定义一个 `create_agent(...)` 对象，再在 `langgraph.json` 的 `graphs` 加一行 `"名字": {"path": "./xxx.py:对象名"}`。

### 后端目录

- `src/core/llms.py`：统一的大模型定义 `ds_llm = ChatDeepSeek(model='deepseek-v4-flash')`，所有 agent 从这里 import，改模型只动这一处。
- `src/agents/test_case_agent.py`：测试用例生成智能体，通过 MCP 客户端（SSE，`http://127.0.0.1:8000/sse`）调用 docling 工具解析文档，按内置 system_prompt 输出 Markdown 表格用例。⚠️ 运行它前需先启动 docling MCP 服务监听 8000 端口（依赖已声明 `docling-mcp[local]`）。
- `src/utils/pdf_parser.py`：目前为空。
- `examples/mcp/`：MCP 客户端/服务端三种传输方式（stdio/sse/http）的示例；`mcp_server.py` 是一个 FastMCP SSE 服务。⚠️ `HTTP_demo.py` 里硬编码了一个 Tavily API key，勿提交。
- `examples/doc_loader_example/`、`examples/langchain_demo/`：PDF 加载（PyMuPDF4LLM + 千问多模态解析图片）与 LangChain 基础用法示例代码。
- `requirements/`、`examples/doc_loader_example/` 下的 `.pdf` 是测试用的需求文档样本。

### 前端目录（web/）

- 单页应用：`src/app/page.tsx` 是入口，对话流核心状态在 `src/app/hooks/useChat.ts`（用 `@langchain/langgraph-sdk/react` 的 `useStream` 驱动）。
- `src/providers/ClientProvider.tsx` 创建 langgraph-sdk 的 `Client`；`ChatProvider.tsx` 包装 `useChat`。
- `src/lib/config.ts`：管理 localStorage 里的连接配置（key `deep-agent-config`，含 deploymentUrl / assistantId / langsmithApiKey）。
- `src/app/components/` 是业务组件（聊天、线程列表、工具调用展示、中断处理），`src/components/ui/` 是 shadcn 风格基础 UI 组件。

### 数据流

前端（Next.js）→ langgraph-sdk → LangGraph API 服务器（`start_server.py`:2026）→ 注册的图（如 `test_case_agent`）→ DeepSeek 大模型 + docling MCP 工具 → 返回测试用例。

## 环境与注意事项

- `.env`（根目录）需要的 key：`DEEPSEEK_API_KEY`、`ZHIPU_API_KEY`、`DASHSCOPE_API_KEY`、`DOCLING_MCP_CONVERSION_MODE`；`start_server.py` 会强制 `PYTHONUTF8=1` 以规避 Windows GBK 解码问题。
- 后端代码用绝对导入 `from src.core.llms import ...`，依赖仓库根目录在 `sys.path` 上（`start_server.py` 已处理；直接 `python src/xxx.py` 单独运行会 import 失败，需从根目录跑）。
- `.langgraph_api/`、`.venv/` 是运行时产物，勿纳入改动范围。
