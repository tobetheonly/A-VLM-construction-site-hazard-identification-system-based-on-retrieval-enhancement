from pymongo import MongoClient
from config import Config
import sys

def test_mongodb_connection():
    """测试MongoDB连接"""
    try:
        print("🔄 正在测试MongoDB连接...")
        
        # 连接MongoDB
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB连接成功！")
        
        # 获取数据库
        db = client[Config.DATABASE_NAME]
        
        # 测试数据库操作
        print(f"📊 数据库名称: {Config.DATABASE_NAME}")
        
        # 检查集合是否存在
        collections = db.list_collection_names()
        print(f"📋 现有集合: {collections}")
        
        # 检查cases集合
        if 'cases' in collections:
            count = db.cases.count_documents({})
            print(f"📈 cases集合文档数量: {count}")
            
            # 显示前几个文档
            sample_docs = list(db.cases.find().limit(3))
            print(f"📄 示例文档:")
            for doc in sample_docs:
                print(f"   - {doc.get('filename', 'N/A')} (类型: {doc.get('type', 'N/A')})")
        else:
            print("⚠️  cases集合不存在，需要运行数据库初始化")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 确保MongoDB服务正在运行")
        print("2. 检查MONGODB_URI配置是否正确")
        print("3. 检查网络连接")
        return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)