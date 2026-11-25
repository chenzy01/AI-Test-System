# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-11-20
# @Description:
# [[]]
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend, FilesystemBackend, CompositeBackend
from rapidocr.cli import root_dir

from core.llms import ds_llm

workspace_dir = Path(__file__).parents[2].resolve() / "workspace" # 工作空间目录
shell_backend = LocalShellBackend(root_dir=workspace_dir,virtual_mode=True)

file_backend = FilesystemBackend(root_dir=workspace_dir,virtual_mode=True) # 文件系统后端
# 混合后端
composite_backend = CompositeBackend(
    default=shell_backend, # 默认使用 shell 执行命令
    routes={"/": file_backend}) # 路径访问文件系统，用来访问skill
# 创建技能中间件
# skill_middleware = SkillMiddleware(
#     backend=file_backend,
#     sources=["/web/skills/playwright-lci"]
# )


agent = create_deep_agent(
    model=ds_llm,
    tools=[],
    # middleware=[skill_middleware],
    skills=["/web/skills/playwright-lci"],
    backend=composite_backend
)


