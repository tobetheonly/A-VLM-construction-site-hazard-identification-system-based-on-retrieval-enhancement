import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # MongoDB配置
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    DATABASE_NAME = 'hazard_detection'
    
    # 模型配置
    CLIP_MODEL_NAME = 'ViT-B/32'  # 使用较小的模型进行测试
    
    # LLM配置（原有字段，暂未直接使用）
    LLM_API_KEY = os.environ.get('LLM_API_KEY') or 'YOUR_DEFAULT_LLM_KEY'
    LLM_MODEL = 'gpt-4-vision-preview'

    # 新增：多模型配置（可用环境变量覆盖）
    # Gemini 通过 OpenRouter 调用
    GEMINI_BASE_URL = os.environ.get('GEMINI_BASE_URL', 'https://openrouter.ai/api/v1')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'sk-or-v1-***************')  # 请替换为你自己的 key
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'google/gemini-2.0-flash-exp:free')

    # GPT-4o 通过 xiaoai.plus 调用
    GPT4O_BASE_URL = os.environ.get('GPT4O_BASE_URL', 'https://xiaoai.plus/v1')
    GPT4O_API_KEY = os.environ.get('GPT4O_API_KEY', 'sk-***********************')  # 请替换为你自己的 key
    GPT4O_MODEL = os.environ.get('GPT4O_MODEL', 'gpt-4o')
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # RAG配置
    SIMILAR_CASES_COUNT = 5
    FEW_SHOT_EXAMPLES_COUNT = 3
    
    # 数据集路径
    DATASET_PATH = 'datasets/隐患数据集/隐患数据集/隐患图片'
    DESCRIPTION_FILE = 'datasets/隐患数据集/隐患数据集/隐患描述文档.txt'
    CATEGORY_FILE = 'datasets/隐患数据集/隐患数据集/隐患类别描述文档.txt'