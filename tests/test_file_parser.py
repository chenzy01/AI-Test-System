"""file_parser 解析入口测试（离线，无网络）。

图片入口 parse_image_base64 依赖多模态大模型，无法离线测试，不在此覆盖。
"""

import base64
import io

import openpyxl

from src.utils.file_parser import parse_csv_base64, parse_text_base64, parse_xlsx_base64


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode()


def test_parse_text_base64():
    assert parse_text_base64(_b64("hello 文本")) == "hello 文本"


def test_parse_csv_base64():
    md = parse_csv_base64(_b64("name,age\n张三,30\n李四,25\n"))
    assert "| name | age |" in md
    assert "张三" in md and "李四" in md


def test_parse_xlsx_base64():
    buf = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["列A", "列B"])
    ws.append(["x", "1"])
    wb.save(buf)

    md = parse_xlsx_base64(base64.b64encode(buf.getvalue()).decode())
    assert "## Sheet1" in md
    assert "列A" in md and "x" in md
