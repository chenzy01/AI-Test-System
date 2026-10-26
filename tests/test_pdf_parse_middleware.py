"""PdfParseMiddleware 测试。

覆盖提示词要求的 a-f 六个场景，另补异步路径与字段兼容测试。
"""

import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import MagicMock

import fitz
from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage

from src.middleware.pdf_parse_middleware import PdfParseMiddleware, _get_field


def _text(content) -> str:
    """从 message content（str 或 block list）提取纯文本。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", ""))
        return "\n".join(parts)
    return ""


def _file_block(mime="application/pdf", data="", filename="doc.pdf") -> dict:
    return {
        "type": "file",
        "mimeType": mime,
        "data": data,
        "metadata": {"filename": filename},
    }


def _make_request(messages, system_message=None) -> ModelRequest:
    return ModelRequest(
        model=MagicMock(), messages=messages, system_message=system_message
    )


def _make_handler(captured):
    def handler(request):
        captured["request"] = request
        return ModelResponse(result=[AIMessage(content="ok")])

    return handler


def test_normal_path_real_pdf():
    """a. 现场生成小 PDF 走真实解析，断言 system_message 含解析出的文本。"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello PDF test content 12345")
    pdf_b64 = base64.b64encode(doc.tobytes()).decode()

    msg = HumanMessage(
        content=[
            {"type": "text", "text": "解析该文档"},
            _file_block(data=pdf_b64, filename="sample.pdf"),
        ],
        id="msg-001",
    )
    captured = {}
    PdfParseMiddleware().wrap_model_call(
        _make_request([msg]), _make_handler(captured)
    )

    sm_text = _text(captured["request"].system_message.content)
    assert "【文档解析结果】《sample.pdf》" in sm_text
    assert "Hello PDF test content 12345" in sm_text


def test_cache_parses_only_once():
    """b. 同一消息 id 连调两次，解析入口只执行一次。"""
    mock_parser = MagicMock(return_value="parsed content")
    mw = PdfParseMiddleware(parsers={"application/pdf": mock_parser})

    msg = HumanMessage(
        content=[_file_block(data="JVBERi0xLjE=", filename="a.pdf")],
        id="msg-cache",
    )

    for _ in range(2):
        captured = {}
        mw.wrap_model_call(_make_request([msg]), _make_handler(captured))
        assert "parsed content" in _text(
            captured["request"].system_message.content
        )

    assert mock_parser.call_count == 1


def test_parse_failure_degrades_gracefully():
    """c. 解析入口抛异常：不崩，system_message 含失败说明。"""

    def boom(_data: str) -> str:
        raise RuntimeError("boom")

    mw = PdfParseMiddleware(parsers={"application/pdf": boom})

    msg = HumanMessage(
        content=[_file_block(data="JVBERi0xLjE=", filename="bad.pdf")],
        id="msg-err",
    )
    captured = {}
    mw.wrap_model_call(_make_request([msg]), _make_handler(captured))

    sm_text = _text(captured["request"].system_message.content)
    assert "【文档解析失败】《bad.pdf》" in sm_text
    assert "boom" in sm_text


def test_no_file_blocks_passthrough():
    """d. 纯文本消息原样透传，不做任何修改。"""
    mw = PdfParseMiddleware()
    msg = HumanMessage(content="纯文本问题")
    captured = {}

    result = mw.wrap_model_call(_make_request([msg]), _make_handler(captured))

    assert captured["request"].system_message is None
    assert captured["request"].messages == [msg]
    assert result.result[0].content == "ok"


def test_strip_removes_base64():
    """e. 剥离后 handler 收到的 messages 不含原始 base64 原文。"""
    raw_b64 = "JVBERi0xLjE="
    mock_parser = MagicMock(return_value="parsed")
    mw = PdfParseMiddleware(parsers={"application/pdf": mock_parser})

    msg = HumanMessage(
        content=[
            {"type": "text", "text": "解析它"},
            _file_block(data=raw_b64, filename="a.pdf"),
        ],
        id="msg-strip",
    )
    captured = {}
    mw.wrap_model_call(_make_request([msg]), _make_handler(captured))

    new_text = _text(captured["request"].messages[0].content)
    assert raw_b64 not in new_text
    assert "[文件已解析：a.pdf，完整内容见系统消息]" in new_text


def test_strip_removes_base64_on_parse_failure():
    """e2. 解析失败/不支持 MIME 时也必须剥离原始 file 块，避免非法 block 透传给模型。"""

    def boom(_data: str) -> str:
        raise RuntimeError("boom")

    raw_b64 = "JVBERi0xLjE="
    mw = PdfParseMiddleware(parsers={"application/pdf": boom})

    cases = [
        (_file_block(data=raw_b64, filename="bad.pdf"), "bad.pdf"),
        (
            _file_block(mime="application/msword", data="ZZZZ", filename="x.doc"),
            "x.doc",
        ),
    ]

    for block, filename in cases:
        msg = HumanMessage(
            content=[{"type": "text", "text": "解析它"}, block],
            id=f"msg-fail-strip-{filename}",
        )
        captured = {}
        mw.wrap_model_call(_make_request([msg]), _make_handler(captured))

        new_content = captured["request"].messages[0].content
        assert all(
            not (isinstance(b, dict) and b.get("type") == "file") for b in new_content
        ), f"{filename} 的 file 块未被剥离"
        assert "[文件解析失败：" in _text(new_content)
        assert filename in _text(new_content)

    # 失败说明仍注入 system message
    sm_text = _text(captured["request"].system_message.content)
    assert "【文档解析失败】" in sm_text


def test_multi_type_files_in_order():
    """f. PDF + 图片混合：两类都被解析且按出现顺序注入。"""
    pdf_parser = MagicMock(return_value="PDF 内容")
    img_parser = MagicMock(return_value="图片内容")
    mw = PdfParseMiddleware(
        parsers={"application/pdf": pdf_parser, "image/": img_parser}
    )

    msg = HumanMessage(
        content=[
            {"type": "text", "text": "两个文件"},
            _file_block(mime="application/pdf", data="AAA", filename="a.pdf"),
            _file_block(mime="image/png", data="BBB", filename="b.png"),
        ],
        id="msg-multi",
    )
    captured = {}
    mw.wrap_model_call(_make_request([msg]), _make_handler(captured))

    pdf_parser.assert_called_once_with("AAA")
    img_parser.assert_called_once_with("BBB")

    sm_text = _text(captured["request"].system_message.content)
    assert "PDF 内容" in sm_text and "图片内容" in sm_text
    assert sm_text.index("a.pdf") < sm_text.index("b.png")


def test_async_wrap_model_call():
    """g. 异步路径：awrap_model_call 正常解析注入。"""
    mock_parser = MagicMock(return_value="async parsed")
    mw = PdfParseMiddleware(parsers={"application/pdf": mock_parser})

    msg = HumanMessage(
        content=[_file_block(data="JVBERi0xLjE=", filename="a.pdf")],
        id="msg-async",
    )
    captured = {}

    async def ahandler(request):
        captured["request"] = request
        return ModelResponse(result=[AIMessage(content="ok")])

    async def run():
        await mw.awrap_model_call(_make_request([msg]), ahandler)

    asyncio.run(run())

    sm_text = _text(captured["request"].system_message.content)
    assert "async parsed" in sm_text


def test_field_name_compatibility():
    """h1. dict 块：mime_type 蛇形 / mimeType 驼峰 + data URI 前缀剥离。"""
    calls = []

    def recorder(data: str) -> str:
        calls.append(data)
        return "内容"

    mw = PdfParseMiddleware(
        parsers={
            "application/pdf": recorder,
            "image/": recorder,
            "text/": recorder,
        }
    )

    snake = {
        "type": "file",
        "mime_type": "image/png",
        "data": "data:image/png;base64,AAAA",
        "metadata": {"filename": "snake.png"},
    }
    camel = {
        "type": "file",
        "mimeType": "application/pdf",
        "data": "BBBB",
        "metadata": {"filename": "camel.pdf"},
    }
    text = {
        "type": "file",
        "mime_type": "text/plain",
        "data": "CCCC",
        "metadata": {"filename": "note.txt"},
    }

    msg = HumanMessage(content=[snake, camel, text], id="msg-compat")
    captured = {}
    mw.wrap_model_call(_make_request([msg]), _make_handler(captured))

    sm_text = _text(captured["request"].system_message.content)
    assert "snake.png" in sm_text
    assert "camel.pdf" in sm_text
    assert "note.txt" in sm_text

    assert len(calls) == 3
    assert "AAAA" in calls  # data URI 前缀已剥离
    assert "data:image/png;base64," not in " ".join(calls)
    assert "BBBB" in calls and "CCCC" in calls


def test_get_field_handles_object_blocks():
    """h2. _get_field 对象块取值：兼容 dict 与对象、多种字段名。"""
    block = SimpleNamespace(
        type="file",
        mime_type="image/png",
        data="AAA",
        base64="BBB",
        metadata={"filename": "obj.png"},
    )

    assert _get_field(block, "type") == "file"
    assert _get_field(block, "mimeType", "mime_type") == "image/png"
    assert _get_field(block, "data") == "AAA"
    assert _get_field(block, "base64") == "BBB"
    assert _get_field(block, "metadata") == {"filename": "obj.png"}

    # dict 块同样适用
    assert _get_field({"type": "file", "mimeType": "text/plain"}, "mimeType", "mime_type") == "text/plain"
    assert _get_field({"type": "file"}, "mimeType", "mime_type") is None
