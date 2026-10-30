# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-10-28
# @Description:
# [[]]
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

documents = TextLoader('tester.txt','utf-8').load()

text_spliter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=30, length_function=len)

spliter_document = text_spliter.split_documents(documents)
