# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-10-29
# @Description:
# [[]]
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest",
    base_url="http://localhost:11434"
)

result = embeddings.embed_query("你好")
# 将“你好”转为了1个向量，768个维度，类型是列表，里面元素都是float
print(result)

two_vectors = embeddings.embed_documents(['你好','hello'])
for vector in two_vectors:
    print(len(vector),vector[:30])

