import os
#import ssl
#import urllib3

# 配置 Hugging Face 镜像源（必须在导入任何使用 huggingface_hub 的模块之前设置）
# 如果遇到 SSL 错误或连接问题，使用镜像源可以解决
#os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 使用 Hugging Face 镜像

# 临时禁用 SSL 验证（仅用于解决连接问题，生产环境不推荐）
# 如果镜像源仍然无法连接，可以取消下面的注释
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# os.environ['CURL_CA_BUNDLE'] = ''
# os.environ['REQUESTS_CA_BUNDLE'] = ''

from flask import Flask, jsonify
from flask_cors import CORS
from routes.analysis import analysis_bp
from routes.history import history_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 启用CORS
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(analysis_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')
    
    # 添加根路径
    @app.route('/')
    def index():
        return jsonify({
            'message': '隐患识别系统API服务',
            'status': 'running',
            'version': '1.0.0',
            'endpoints': {
                'analysis': '/api/analyze',
                'history': '/api/history',
                'health': '/api/health'
            }
        })
    
    # 添加健康检查端点
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': '2024-01-01T10:00:00Z'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)