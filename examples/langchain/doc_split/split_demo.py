# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-10-28
# @Description:
# [[]]
from langchain_text_splitters import RecursiveCharacterTextSplitter
content = """
1. **全链路追溯矩阵**：需求→测试点→用例→执行→报告→缺陷，一个 ID 贯穿到底。任何环节产物都能向前溯源、向后追踪 —— 这是保真的骨架。黄金集回归基线（Golden Set）**：把人工确认真实正确的历史交付物沉淀成基线，每次新产出与基线比对结构 / 质量，防模型版本升级导致的质量退化。
**双轨校验**：确定性校验（格式、ID 唯一性、数字对账 —— 用脚本，可断言）+ 生成式校验（评审 Agent/LLM 裁判 —— 看语义质量），两类互补，确定性校验永远不能省。
**分层人工在环（HITL）**：AI 自检 → 评审 Agent → 人工抽审（关键交付物全审、常规交付物抽审），每层职责明确，人工只审机器审不了的部分。
"""
# 递归文本分割器
text_spliter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=30, length_function=len)
"""
chunk_size: 每个 chunk 的大小,最大是 100 个字符
chunk_overlap: 两个 chunk 之间的重叠部分的大小
length_function: 计算长度（chunk_size、chunk_overlap）的函数
分割原理：源代码中 self._separators = separators or ["\n\n", "\n", " ", ""]，即先按 "\n\n" 分割，如果分割后第一部分
超过了100个字符，则继续对第一部分进行分割继续使用"\n\n"进行分割，如果 "\n\n" 不存在则按 "\n" 分割，
如果 "\n" 也不存在则按 " " 分割，如果 " " 也不存在则按 "" 分割
"""
# 存储多个文本块
split_text = text_spliter.split_text(content)
print(type(split_text), split_text)

# 转化为文档对象
split_document = text_spliter.create_documents(split_text)
print(type(split_document), split_document)