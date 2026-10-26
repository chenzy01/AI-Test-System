import os

from dotenv import load_dotenv

# from langchain_pymupdf4llm import PyMuPDF4LLMLoader
#
# loader = PyMuPDF4LLMLoader(
#     "电商平台购物车功能需求文档（精简版）.pdf",
#     mode='single' # single 把所有内容都放到也给对象中，page 一个页面就是一个文档对象
# )
#
# doc = loader.load()
# print(doc)


# 用多模态大模型加载PDF
# 官网示例代码
"""
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_openai import ChatOpenAI

loader = PyMuPDF4LLMLoader(
    "test.pdf",
    mode="page",
    extract_images=True,
    images_parser=LLMImageBlobParser(
        model=ChatOpenAI(model="gpt-5.5", max_tokens=1024),
        prompt="Describe the content of each image in a few sentences."
    ),
)
docs = loader.load()

print(docs[0].page_content[0:])
"""
# 改为使用千问多模态大模型
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_openai import ChatOpenAI
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

loader = PyMuPDF4LLMLoader(
    "小狗介绍.pdf",
    mode="page",
    extract_images=True,
    table_strategy="lines",  # 如有表格识别，用这个参数
    images_parser=LLMImageBlobParser(
        model=ChatOpenAI(
            model="qwen3.8-omni-flash",
            base_url="https://maas.qianwenaiapi.com/compatible-mode/v1", # https://dashscope.aliyun.com/compatible-mode/v1
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            ),
        prompt=IMAGE_DESCRIPTION_PROMPT,
    ),
)
docs = loader.load()
print(docs[0].page_content[0:])
