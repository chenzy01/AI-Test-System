"""自定义中间件：模型调用前解析用户消息中的文件并注入 SystemMessage。

设计目标：
- 前端（Deep Agents UI）上传的文件以 ``type=='file'`` 内容块塞进 HumanMessage，
  内含 base64 原文。若直接交模型，base64 体积约为原文件 1.37 倍，导致 token 爆炸。
- 本中间件在每次模型调用前拦截请求：提取 file 块 -> 统一转 base64 ->
  按 MIME 分发到解析入口 -> 解析结果追加进 SystemMessage -> 剥离原始 base64 -> 缓存。

注册示例::

    from langchain.agents import create_agent
    from src.core.llms import ds_llm
    from src.middleware.pdf_parse_middleware import PdfParseMiddleware

    agent = create_agent(model=ds_llm, middleware=[PdfParseMiddleware()])
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import BaseMessage, SystemMessage

from src.utils.file_parser import (
    parse_csv_base64,
    parse_image_base64,
    parse_text_base64,
    parse_xlsx_base64,
)
from src.utils.pdf_parser import parse_pdf_base64

logger = logging.getLogger(__name__)

# 解析入口统一契约：入参 base64 字符串 -> 返回 Markdown 全文。
Parser = Callable[[str], str]

# 默认分发注册表：MIME 类型（或 ``xxx/`` 前缀）-> 解析函数。
# 扩展新文件类型时，往这里注册对应入口即可，中间件调用逻辑不变。
DEFAULT_PARSERS: dict[str, Parser] = {
    "application/pdf": parse_pdf_base64,
    "image/": parse_image_base64,
    "text/csv": parse_csv_base64,
    "application/csv": parse_csv_base64,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": parse_xlsx_base64,
    "text/": parse_text_base64,
}


def _get_field(block: Any, *names: str) -> Any:
    """从内容块（dict 或对象）读取字段，兼容多种命名。"""
    if isinstance(block, dict):
        for name in names:
            if name in block:
                return block[name]
    for name in names:
        if hasattr(block, name):
            return getattr(block, name)
    return None


@dataclass
class _FileEntry:
    """一次模型调用里提取到的单个文件块。"""

    msg_index: int
    block_index: int
    filename: str
    mime: str | None
    data: str
    key: str
    parser: Parser | None
    ok: bool = False


class PdfParseMiddleware(AgentMiddleware):
    """模型调用前解析文件内容并注入 SystemMessage 的中间件。

    Args:
        strip_source_blocks: 是否剥离消息中的 base64 原文（默认开启）。
        parsers: 自定义 MIME -> 解析函数 注册表；默认用 ``DEFAULT_PARSERS``。
    """

    def __init__(
        self,
        strip_source_blocks: bool = True,
        parsers: dict[str, Parser] | None = None,
    ) -> None:
        super().__init__()
        self.strip_source_blocks = strip_source_blocks
        self._parsers: dict[str, Parser] = (
            dict(parsers) if parsers is not None else dict(DEFAULT_PARSERS)
        )
        self._cache: dict[str, str] = {}

    # ---------- 纯函数辅助 ----------

    @staticmethod
    def _normalize_base64(data: Any) -> str:
        """把前端数据统一转换为纯 base64 字符串（剥离 data URI 前缀）。"""
        if data is None:
            return ""
        if isinstance(data, (bytes, bytearray)):
            return base64.b64encode(bytes(data)).decode("ascii")
        text = data if isinstance(data, str) else str(data)
        text = text.strip()
        if "," in text and text.lower().startswith("data:"):
            text = text.split(",", 1)[1]
        return text

    def _resolve_parser(self, mime: str | None) -> Parser | None:
        """按 MIME 类型解析到对应入口：先精确匹配，再按 ``xxx/`` 前缀最长匹配。"""
        if not mime:
            return None
        mime = mime.lower()
        if mime in self._parsers:
            return self._parsers[mime]
        for prefix in sorted(self._parsers, key=len, reverse=True):
            if prefix.endswith("/") and mime.startswith(prefix):
                return self._parsers[prefix]
        return None

    def _cache_key(self, message: BaseMessage, block_index: int, data: str) -> str:
        """缓存 key：优先消息 id，无 id 时用 base64 数据的 sha1。"""
        msg_id = getattr(message, "id", None)
        if msg_id:
            return f"{msg_id}:{block_index}"
        return f"sha1:{hashlib.sha1(data.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _extract_filename(block: Any) -> str:
        """取 metadata.filename，缺失时默认 'document'。"""
        metadata = _get_field(block, "metadata")
        filename = _get_field(metadata, "filename") if metadata is not None else None
        return str(filename) if filename else "document"

    def _extract_entries(self, messages: list[BaseMessage]) -> list[_FileEntry]:
        """遍历所有消息的 list 型 content，提取全部 type=='file' 内容块。"""
        entries: list[_FileEntry] = []
        for mi, message in enumerate(messages):
            content = getattr(message, "content", None)
            if not isinstance(content, list):
                continue
            for bi, block in enumerate(content):
                if _get_field(block, "type") != "file":
                    continue
                data = self._normalize_base64(
                    _get_field(block, "data", "base64", "url")
                )
                mime = _get_field(block, "mimeType", "mime_type")
                entries.append(
                    _FileEntry(
                        msg_index=mi,
                        block_index=bi,
                        filename=self._extract_filename(block),
                        mime=mime,
                        data=data,
                        key=self._cache_key(message, bi, data),
                        parser=self._resolve_parser(mime),
                    )
                )
        return entries

    # ---------- 注入 / 剥离 ----------

    @staticmethod
    def _success_section(filename: str, content: str) -> str:
        return f"【文档解析结果】《{filename}》\n\n{content}"

    @staticmethod
    def _failure_section(filename: str, err: str) -> str:
        return (
            f"【文档解析失败】《{filename}》解析出错：{err}。"
            "请基于用户文本请求回答，并提示用户文档暂时无法解析。"
        )

    @staticmethod
    def _build_system_message(
        existing: SystemMessage | None, injected: str
    ) -> SystemMessage:
        """保留原 system message 内容，末尾追加一个 text block；无则新建。"""
        new_block = {"type": "text", "text": injected}
        if existing is None:
            return SystemMessage(content=[new_block])
        old = existing.content
        if isinstance(old, str):
            blocks = [{"type": "text", "text": old}, new_block]
        elif isinstance(old, list):
            blocks = list(old) + [new_block]
        else:
            blocks = [new_block]
        return existing.model_copy(update={"content": blocks})

    def _strip_messages(
        self, messages: list[BaseMessage], entries: list[_FileEntry]
    ) -> list[BaseMessage]:
        """把 file 块统一替换为轻量文本块（成功/失败都替换），其余 blocks 原样保留。

        失败块也必须替换：原始块含 base64 的 ``data`` 字段，多数模型接口
        （如 DeepSeek 的 OpenAI 兼容端点）要求 file 块提供 file_id/file_data，
        保留原文会直接导致 400。
        """
        if not self.strip_source_blocks:
            return messages
        by_message: dict[int, dict[int, _FileEntry]] = {}
        for entry in entries:
            by_message.setdefault(entry.msg_index, {})[entry.block_index] = entry

        new_messages = list(messages)
        for mi, block_map in by_message.items():
            message = messages[mi]
            new_blocks = []
            for bi, block in enumerate(message.content):
                entry = block_map.get(bi)
                if entry is None:
                    new_blocks.append(block)
                elif entry.ok:
                    new_blocks.append(
                        {
                            "type": "text",
                            "text": (
                                f"[文件已解析：{entry.filename}，完整内容见系统消息]"
                            ),
                        }
                    )
                else:
                    new_blocks.append(
                        {
                            "type": "text",
                            "text": (
                                f"[文件解析失败：{entry.filename}，"
                                "原始文件未提交给模型，失败原因见系统消息]"
                            ),
                        }
                    )
            new_messages[mi] = message.model_copy(update={"content": new_blocks})
        return new_messages

    # ---------- 单文件解析（查缓存 -> 解析 -> 写缓存）----------

    def _parse_one(self, entry: _FileEntry, invoke: Callable[[Parser, str], str]) -> str:
        """对单个文件执行解析，返回注入段。invoke(parser, data) -> str 同步。"""
        if entry.key in self._cache:
            entry.ok = True
            return self._success_section(entry.filename, self._cache[entry.key])
        if entry.parser is None:
            entry.ok = False
            return self._failure_section(
                entry.filename, f"不支持的 MIME 类型：{entry.mime or '未知'}"
            )
        try:
            content = invoke(entry.parser, entry.data)
        except Exception as exc:
            entry.ok = False
            logger.error("解析文件 %s 失败", entry.filename, exc_info=True)
            return self._failure_section(entry.filename, str(exc))
        self._cache[entry.key] = content
        entry.ok = True
        return self._success_section(entry.filename, content)

    async def _aparse_one(
        self, entry: _FileEntry, invoke: Callable[[Parser, str], Awaitable[str]]
    ) -> str:
        """异步版单文件解析，invoke(parser, data) 返回 Awaitable。"""
        if entry.key in self._cache:
            entry.ok = True
            return self._success_section(entry.filename, self._cache[entry.key])
        if entry.parser is None:
            entry.ok = False
            return self._failure_section(
                entry.filename, f"不支持的 MIME 类型：{entry.mime or '未知'}"
            )
        try:
            content = await invoke(entry.parser, entry.data)
        except Exception as exc:
            entry.ok = False
            logger.error("解析文件 %s 失败", entry.filename, exc_info=True)
            return self._failure_section(entry.filename, str(exc))
        self._cache[entry.key] = content
        entry.ok = True
        return self._success_section(entry.filename, content)

    # ---------- 汇总构建新请求 ----------

    def _finalize(
        self, request: ModelRequest, entries: list[_FileEntry], sections: list[str]
    ) -> ModelRequest:
        injected = "\n\n".join(sections)
        new_sm = self._build_system_message(request.system_message, injected)
        new_messages = self._strip_messages(request.messages, entries)
        return request.override(system_message=new_sm, messages=new_messages)

    # ---------- 同步 / 异步 hook ----------

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        entries = self._extract_entries(request.messages)
        if not entries:
            return handler(request)
        sections = [
            self._parse_one(entry, lambda parser, data: parser(data))
            for entry in entries
        ]
        return handler(self._finalize(request, entries, sections))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        entries = self._extract_entries(request.messages)
        if not entries:
            return await handler(request)

        async def invoke(parser: Parser, data: str) -> str:
            # 解析是阻塞函数（含网络 IO），必须在事件循环外执行
            return await asyncio.to_thread(parser, data)

        sections = [await self._aparse_one(entry, invoke) for entry in entries]
        return await handler(self._finalize(request, entries, sections))
