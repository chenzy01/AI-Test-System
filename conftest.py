import sys
from pathlib import Path

# 项目根目录加入 sys.path，测试内可用 `from src...` 绝对导入
sys.path.insert(0, str(Path(__file__).resolve().parent))
