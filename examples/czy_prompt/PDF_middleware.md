# 角色
资深 LangChain 1.x / LangGraph 工程师，熟悉 Agent 中间件机制。

# 任务
在 czy-ai-system 项目中实现一个自定义中间件 `PdfParseMiddleware`：每次模型调用前，自动从用户消息中提取文件数据并统一转为 base64 → 调用解析入口得到完整文档内容 → 追加进 SystemMessage → 再交给模型。支持 PDF、图片等全类型文件。参考文档：https://docs.langchain.com/oss/python/langchain/middleware/custom#class-based-middleware

# 已核实上下文（直接用，不要重新查证）
## 环境
- 项目根目录 D:/PycharmProjects/czy-ai-system，langchain 1.3.16（要求 >= 1.0），venv 在 .venv/
- 导入路径（已验证可导入）：
  - `from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse`
  - `from langchain.messages import SystemMessage`
  - `from src.utils.pdf_parser import parse_pdf_base64`

## 解析器（src/utils/pdf_parser.py，可适当修改，但修改前要经过同意）
`parse_pdf_base64(pdf_base64: str, model=None, base_url=None, api_key=None) -> str`
- 接收纯 base64 字符串，兼容 `data:application/pdf;base64,` 前缀；内部自动写临时文件并清理
- 返回整份 PDF 的 Markdown 全文（PyMuPDF4LLM + 多模态模型解析图片）
- 空数据抛 ValueError，解析失败抛异常；是阻塞函数（含网络 IO），异步上下文必须用 asyncio.to_thread 包装
- 解析入口统一契约：**入参 base64 字符串 → 返回 Markdown 全文**。当前只有 PDF 有入口（parse_pdf_base64）；图片等其他类型的解析入口按同一契约扩展（扩展现有模块或新增模块均可，扩展前须经同意），中间件调用方式不因入口扩展而改变

## 中间件 API（已验证，langchain 1.3.16）
- 基类 AgentMiddleware；本需求用 wrap 型 hook：
  - `def wrap_model_call(self, request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ModelResponse`
  - 异步版 `async def awrap_model_call(self, request, handler) -> ModelResponse`
- ModelRequest 字段：model、messages（不含 system message）、system_message: SystemMessage | None、tools、state、runtime 等
- `request.override(system_message=..., messages=...)` 返回新请求（不可变模式），再传给 handler
- 中间件实例在 create_agent 时注册，agent 循环中每次模型调用都会触发（含工具调用后的后续轮次）——必须做缓存，否则同一文件会被反复解析

## 前端消息格式实例
```python
HumanMessage(content=[
  {'type': 'text', 'text': '解析该文档'},
  {'type': 'file', 'mimeType': 'application/pdf', 'data': 'JVBERi0xLjcK...', 'metadata': {'filename': 'xxx.pdf'}}
], id='e64d0d53-...')
```
注意：① content block 可能是 dict 也可能是对象，MIME 字段名可能是 mimeType 或 mime_type，实现时两种都要兼容；② file 块不限于 PDF，也可能是图片（image/png 等）、文本、表格等类型，一律按 type=='file' 统一处理，不按 MIME 过滤。

# 功能需求
## F1 提取与注入
- 遍历 request.messages 中所有消息的 content（仅处理 list 型 content），找出所有 type=='file' 的文件块——不限定 MIME 类型，PDF、图片、文本、表格等全类型均在处理范围内
- 中间件负责把前端传来的文件数据统一转换为 base64 字符串（含剥离 data URI 前缀等规范化处理）；取 metadata.filename（缺失时默认 'document'）
- 将规范化后的 base64 送入解析入口得到完整内容（解析契约为入参 base64、返回 Markdown 全文；当前 PDF 走 parse_pdf_base64，其他类型走按同一契约扩展的入口）
- 注入 SystemMessage：
  - 已存在 system_message：保留原 content blocks，末尾追加一个 text block
  - 不存在：新建 SystemMessage
  - 每个文件一段，格式：`【文档解析结果】《{filename}》\n\n{content}`，多个文件按出现顺序排列
- 调用 `handler(request.override(system_message=new_sm))` 并原样返回其结果

## F2 剥离 base64 原文（默认开启，通过 __init__ 参数 strip_source_blocks: bool = True 控制）
- 解析成功后，把该消息里的 file 块替换为轻量文本块：`[文件已解析：{filename}，完整内容见系统消息]`
- 原始 base64 严禁传给模型（base64 体积约为原始文件的 1.37 倍，直接进上下文会造成 token 爆炸和费用飙升）
- 消息其余 blocks（如用户的 text 提问）保持不变

## F3 解析缓存
- 在中间件实例上维护 dict 缓存：key 优先取消息 id，无 id 时对 base64 数据取 sha1 哈希；命中缓存直接复用，不重复调用解析入口

## F4 异常降级（不得让解析失败崩溃整个 agent）
- 解析入口抛异常时：记录 error 日志（含 filename 和 traceback），并在 SystemMessage 追加：`【文档解析失败】《{filename}》解析出错：{err}。请基于用户文本请求回答，并提示用户文档暂时无法解析。`
- 原消息不动，继续正常调用模型

## F5 其他边界（全类型文件）
- 处理边界覆盖前端传来的所有文件块：PDF、图片、文本、表格等都在支持范围内——底层是多模态解析能力，文本、图片、表格都支持解析，不再限定 application/pdf
- 中间件的核心职责之一：把前端传过来的文件数据统一转换为 base64；转换为 base64 之后的处理逻辑与本 Prompt 其他章节完全一致（解析 → 注入 SystemMessage → 剥离原文 → 缓存 → 异常降级），不因文件类型不同而改变
- 消息中没有任何 file 块：`return handler(request)` 原样放行，不做任何修改
- 同一消息包含多个文件（可混合不同类型）：全部解析，按出现顺序注入

## F6 同步/异步双实现
- wrap_model_call 中直接调用解析入口
- awrap_model_call 中用 `await asyncio.to_thread(解析入口, data)` 包装（解析是阻塞函数，禁止在事件循环中同步调用）

# 实现约束
1. 扩展/修改解析入口前须经用户同意（不经同意不得改动 src/utils/pdf_parser.py）
2. 新建 src/middleware/pdf_parse_middleware.py，类名 PdfParseMiddleware，docstring 与类型标注齐全
3. 不需要自定义 state_schema（不扩展 agent state）
4. 日志用标准 logging，logger 名取模块名
5. 代码风格与项目现有代码保持一致

# 交付物
1. src/middleware/pdf_parse_middleware.py 完整实现
2. `create_agent(model=..., middleware=[PdfParseMiddleware()])` 注册示例（放 docstring 或单独说明）
3. 测试（放项目现有测试目录），至少覆盖：
   a. 正常路径：现场生成小 PDF 转 base64 构造 HumanMessage，断言 system_message 含解析出的文本
   b. 缓存路径：连续调用两次，monkeypatch 计数断言解析入口只执行一次
   c. 异常路径：mock 解析入口抛异常，断言不崩溃且 system_message 含失败说明
   d. 无文件路径：纯文本消息原样透传
   e. 剥离路径：断言传给 handler 的 messages 中不含原始 base64 字符串
   f. 多类型路径：构造 PDF + 图片混合的 file 块（mock 解析入口），断言两类都被处理且按出现顺序注入
4. 运行测试，贴出全部通过的结果

# 验收标准
- [ ] 上述 6 个测试全部通过
- [ ] 模型实际收到的消息中不含 base64 原文
- [ ] 同一文件在 agent 多轮循环中只解析一次
- [ ] 解析失败时 agent 仍能正常返回响应