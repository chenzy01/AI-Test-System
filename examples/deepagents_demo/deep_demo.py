# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-10-26
# @Description:
# [[]]
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


from src.core.llms import ds_llm


# 步骤1，backend(后端)，设置skill所在的路径
current_dir = Path(__file__).parent.resolve()  # 获取当前文件的目录绝对路径 D:\PycharmProjects\czy-ai-system\examples\deepagents_demo
# 创建一个文件管理器
file_backend = FilesystemBackend(root_dir=current_dir, virtual_mode=True) # virtual_mode=True 表示只会在 current_dir 目录下查找skill, 默认是False，表示会递归查找

# 步骤2，创建 deep agent 并设置skill 所在的目录
agent = create_deep_agent(
    model=ds_llm,
    backend=file_backend,
    skills=['skills'],
    system_prompt="""你是一个智能助手，可以使用skill技能"""

)