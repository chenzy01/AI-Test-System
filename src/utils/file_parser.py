"""通用文件解析入口（图片 / 文本 / 表格）。

与 `src.utils.pdf_parser.parse_pdf_base64` 遵循同一契约：
入参 base64 字符串 -> 返回 Markdown 全文。

PDF 入口在 `src.utils.pdf_parser`；本模块补齐其余类型，供
`src.middleware.pdf_parse_middleware.PdfParseMiddleware` 按 MIME 类型分发调用。
"""

import base64
import csv
import io
import os

from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_core.documents.base import Blob
from langchain_openai import ChatOpenAI

from src.utils.pdf_parser import (
    DEFAULT_PDF_BASE_URL,
    DEFAULT_PDF_MODEL,
    IMAGE_DESCRIPTION_PROMPT,
)


def _decode_base64(data: str) -> bytes:
    """把 base64 数据解码为字节，兼容 data URI 前缀。"""
    text = (data or "").strip()
    # 兼容 "data:application/pdf;base64,xxxx" 形式的 data URI
    if "," in text and text.lower().startswith("data:"):
        text = text.split(",", 1)[1]
    return base64.b64decode(text, validate=False)


def _sniff_image_mime(raw: bytes) -> str:
    """按魔数嗅探图片 MIME，供多模态解析构造 data URI。"""
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _to_markdown_table(rows: list[list[str]]) -> str:
    """把二维字符串列表转为 Markdown 表格（自动按最宽行补齐列）。"""
    if not rows:
        return ""
    ncols = max(len(row) for row in rows)

    def pad(row: list[str]) -> list[str]:
        row = list(row) + [""] * (ncols - len(row))
        return [cell.replace("|", "\\|") for cell in row]

    header = pad(rows[0])
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * ncols) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(pad(row)) + " |")
    return "\n".join(lines)


def parse_image_base64(
    img_base64: str,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """解析 base64 图片，返回图片内容的 Markdown 描述。

    与 parse_pdf_base64 使用同一套多模态模型（默认千问兼容端点），
    借助 LLMImageBlobParser 提取图片中的文字、结构、细节。
    """
    raw = _decode_base64(img_base64)
    parser = LLMImageBlobParser(
        model=ChatOpenAI(
            model=model or DEFAULT_PDF_MODEL,
            base_url=base_url or DEFAULT_PDF_BASE_URL,
            api_key=api_key or os.getenv("DASHSCOPE_API_KEY"),
        ),
        prompt=IMAGE_DESCRIPTION_PROMPT,
    )
    blob = Blob(data=raw, mimetype=_sniff_image_mime(raw))
    docs = list(parser.lazy_parse(blob))
    return docs[0].page_content if docs else ""


def parse_text_base64(text_base64: str, encoding: str = "utf-8") -> str:
    """解析 base64 文本，返回解码后的全文。"""
    raw = _decode_base64(text_base64)
    return raw.decode(encoding, errors="replace")


def parse_csv_base64(csv_base64: str, encoding: str = "utf-8") -> str:
    """解析 base64 CSV，返回 Markdown 表格。"""
    text = parse_text_base64(csv_base64, encoding=encoding)
    rows = list(csv.reader(io.StringIO(text)))
    return _to_markdown_table(rows)


def parse_xlsx_base64(xlsx_base64: str) -> str:
    """解析 base64 XLSX，逐 sheet 返回 Markdown 表格。"""
    import openpyxl

    raw = _decode_base64(xlsx_base64)
    workbook = openpyxl.load_workbook(
        io.BytesIO(raw), read_only=True, data_only=True
    )
    parts: list[str] = []
    for sheet in workbook.worksheets:
        rows = [
            ["" if cell is None else str(cell) for cell in row]
            for row in sheet.iter_rows(values_only=True)
        ]
        if not rows:
            continue
        parts.append(f"## {sheet.title}\n\n{_to_markdown_table(rows)}")
    return "\n\n".join(parts)
