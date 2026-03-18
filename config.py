import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask 配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'homesignin-secret-key-change-in-production')

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data", "homesignin.db")}')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 数据文件路径（保留用于迁移脚本和向后兼容）
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CHECKINS_FILE = os.path.join(DATA_DIR, 'checkins.json')
QUOTES_FILE = os.path.join(DATA_DIR, 'quotes.json')

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# AI 模型 API 配置
AI_API_KEY = os.environ.get('AI_API_KEY', '')
AI_API_BASE_URL = os.environ.get('AI_API_BASE_URL', 'https://api.anthropic.com/v1')
AI_MODEL = os.environ.get('AI_MODEL', 'claude-sonnet-4-20250514')
