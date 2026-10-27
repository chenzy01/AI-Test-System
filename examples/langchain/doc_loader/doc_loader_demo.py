# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-10-27
# @Description:
# [[]]
from langchain_community.document_loaders import PyPDFLoader

# from langchain_community.document_loaders import TextLoader
#
# file_path = "tester.txt"
# encoding = "utf-8"
# docs = TextLoader(file_path, encoding).load()
# print(docs)

docs = PyPDFLoader(
    file_path="电商平台购物车功能需求文档（精简版）.pdf",
    extraction_mode="plain"  # plain 提取文本，layout 按布局提取
).load()

print(docs)