#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: kun
@created: 2026/8/29
@description: 
"""
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore

embedding_client = DashScopeEmbeddings(
    model="text-embedding-v4",  # 向量模型
    dashscope_api_key =""
)
# 
# text = "This is a test document."
# 
# query_result = embeddings.embed_query(text)
# print("文本向量长度：", len(query_result), query_result[:10])

# texts= [
#     '我喜欢吃苹果',
#     '苹果是我最喜欢吃的水果',
#     '我喜欢用苹果手机'
# ]

# embeddings = embedding_client.embed_documents(texts)
# print(type(embeddings),embeddings[:100])

# 定义每条文本对应的元数据信息
# metadata = [{'segment_id':'1'},{'segment_id':'2'},{'segment_id':'3'}]

# 配置redis 链接参数和索引名称
config = RedisConfig(
    index_name="xly",
    redis_url='redis://localhost:26379',
)

# 创建redis  向量存储实例
vector_store = RedisVectorStore(embedding_client, config=config)

# 将文本信息和元数据 存入到 redis 中
# ids = vector_store.add_texts(texts, metadata)
# print(ids)

# 查询文本
query = '我喜欢用什么手机'

# 将查询语句向量化，并在redis 中 做相似性检查
results  = vector_store.similarity_search_with_score(query, k=3)

for i ,(doc, score) in enumerate(results, 1):
    print(f'结果 {i}:')
    print(f'内容: {doc.page_content}')
    print(f'元数据：{doc.metadata}')
    print(f'相似度：{1-score}')

