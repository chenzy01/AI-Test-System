# -*- coding: utf-8 -*-
# @Author: chenzy
# @Date:   2026-11-19
# @Description:
# [[]]
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from core.llms import ds_llm

backend_agent = create_deep_agent(
    model= ds_llm,
    backend=LocalShellBackend(root_dir="D:\\PycharmProjects\\czy-ai-system\\examples",
                              virtual_mode=True),
)
