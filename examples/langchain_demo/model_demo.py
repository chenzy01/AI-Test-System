import os

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from openai.types.shared_params import reasoning

load_dotenv()
from langchain.chat_models import init_chat_model
from openai import api_key, base_url

# 通用的写法
llm = init_chat_model(
    model = 'deepseek-v4-flash',
    # open_provider = 'openai',
    api_key = os.getenv('DEEPSEEK_API_KEY'), # 要先加载环境变量，才能用到 deepseek_api_key
    base_url = 'https://api.deepseek.com'
)

print(llm.invoke("介绍下深圳近期天气"))

# 如有本地私有化部署，用下面写法
# ollama_llm = ChatOllama(
#     model = 'qwen2.5:0.5b',
#     base_url="http://180.*.*.*:1111"
#     reasoning=False
# )


# deepseek 定制写法，没有写base_url,已经有默认的了；没有写API_KEY，它自己会到环境变量中去查找（.env）
ds_llm = ChatDeepSeek(
    model = 'deepseek-v4-flash',
    temperature=0,
    max_tokens=None,
    timeout=0,
    max_retries=2
)