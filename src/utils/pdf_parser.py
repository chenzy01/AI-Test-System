"""PDF 文档处理器。

接收 BASE64 编码的 PDF 数据，借助 PyMuPDF4LLM + 多模态大模型解析图片，
最终返回完整的文档内容（Markdown 文本）。
"""

import base64
import os

from dotenv import load_dotenv
from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_core.documents.base import Blob
from langchain_openai import ChatOpenAI
from langchain_pymupdf4llm import PyMuPDF4LLMParser

load_dotenv()

IMAGE_DESCRIPTION_PROMPT = (
    "你是一个专业的文档图像解析助手，负责为 PDF 文档中的图片生成高质量的文本描述，"
    "该描述将用于后续的文档检索与问答。请严格完成以下分析:\n"
    "1、整体内容:判断图片类型(如界面原型图、流程图、架构图、表格、截图、照片等)，"
    "并详细描述图片展示的主要内容。\n"
    "2.文字提取:完整提取图片中出现的所有文字，包括标题、按钮文案、表格内容、注释等，"
    "不得遗漏或概括。\n"
    "3.结构信息:如果是表格，逐行逐列描述;如果是流程图，按节点和箭头方向描述流程;"
    "如果是界面图，按区域(顶部导航、主体、底部等)描述布局和交互元素。\n"
    "4.关键细节:记录颜色、状态标识、数字、日期等对理解文档有意义的细节。\n"
    "要求:使用与原文一致的语言(中文内容用中文描述);输出为 markdown 格式， "
    "不要输出任何解释性文字，不要用代码块包裹。")

# 图片解析用的多模态模型（可被调用方覆盖）
DEFAULT_PDF_MODEL = "qwen3.8-omni-flash"
DEFAULT_PDF_BASE_URL = "https://maas.qianwenaiapi.com/compatible-mode/v1"


def _decode_base64(pdf_base64: str) -> bytes:
    """把 base64 PDF 数据解码为字节，兼容 data URI 前缀。"""
    data = pdf_base64.strip()
    # 兼容 "data:application/pdf;base64,xxxx" 形式的 data URI
    if "," in data and data.lower().startswith("data:"):
        data = data.split(",", 1)[1]
    raw = base64.b64decode(data, validate=False)
    if not raw:
        raise ValueError("PDF 数据为空，请检查传入的 base64 内容")
    return raw


def parse_pdf_base64(
    pdf_base64: str,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """解析 base64 PDF 数据，返回完整文档内容。

    参数：
        pdf_base64: PDF 文件的 base64 编码字符串（可含 data URI 前缀）
        model: 图片解析用的多模态模型，默认 qwen3.8-omni-flash
        base_url: 模型服务地址，默认千问兼容端点
        api_key: 模型 API key，默认取环境变量 DASHSCOPE_API_KEY

    返回：
        完整文档内容字符串（single 模式下整份 PDF 合并为一个对象）
    """
    raw = _decode_base64(pdf_base64)

    # 用内存字节流解析，避免落盘临时文件（Windows 下 fitz 不释放句柄，
    # 解析完删除临时文件会抛 PermissionError）
    parser = PyMuPDF4LLMParser(
        mode="single",            # 整份 PDF 合并为一个文档对象，页间由 pages_delimiter 分隔
        extract_images=True,
        table_strategy="lines",   # 如有表格，按线识别
        use_ocr=False,            # 图片走 qwen 多模态解析，无需本地 OCR；关闭后跳过 tesseract 探测，避免 Windows 下 GBK 解码报错
        images_parser=LLMImageBlobParser(
            model=ChatOpenAI(
                model=model or DEFAULT_PDF_MODEL,
                base_url=base_url or DEFAULT_PDF_BASE_URL,
                api_key=api_key or os.getenv("DASHSCOPE_API_KEY"),
            ),
            prompt=IMAGE_DESCRIPTION_PROMPT,
        ),
    )
    blob = Blob(data=raw, mimetype="application/pdf")
    docs = list(parser.lazy_parse(blob))
    return docs[0].page_content if docs else ""
