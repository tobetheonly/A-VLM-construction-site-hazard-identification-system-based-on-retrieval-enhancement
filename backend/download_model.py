# """
# BERT 模型下载脚本
# 如果 Git LFS 下载失败，可以使用此脚本通过 Python 下载模型
# """
# import os
# import sys
# import ssl
# import urllib3

# # 临时禁用 SSL 验证（仅用于解决连接问题）
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# ssl._create_default_https_context = ssl._create_unverified_context


# # 设置镜像源
# #os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# try:
#     from huggingface_hub import snapshot_download
# except ImportError:
#     print("❌ 错误: 未安装 huggingface_hub")
#     print("请运行: pip install huggingface_hub")
#     sys.exit(1)

# def download_model():
#     """下载 BERT 模型"""
#     model_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#     local_dir = "./models/paraphrase-multilingual-MiniLM-L12-v2"
    
#     print("="*60)
#     print("🔄 开始下载 BERT 模型")
#     print("="*60)
#     print(f"模型: {model_id}")
#     print(f"保存到: {local_dir}")
#     print(f"镜像源: {os.environ.get('HF_ENDPOINT', '默认')}")
#     print("="*60)
#     print("\n⚠️  注意: 模型文件较大（约 471 MB），下载可能需要一些时间...")
#     print("如果下载失败，请检查网络连接或尝试使用 VPN\n")
    
#     try:
#         # 创建目录
#         os.makedirs(os.path.dirname(local_dir), exist_ok=True)
        
#         # 下载模型
#         snapshot_download(
#         repo_id=model_id,
#         local_dir=local_dir,
#         local_dir_use_symlinks=False,
#         resume_download=True,
#         token=None,  # 如果不需要认证
#         # 添加这个参数来禁用 SSL 验证
#         ignore_patterns=["*.git*", "*.md"]  # 可选：忽略某些文件
#         )
        
#         print("\n" + "="*60)
#         print("✅ 模型下载完成！")
#         print("="*60)
#         print(f"模型位置: {os.path.abspath(local_dir)}")
#         print("\n现在可以运行应用了: python app.py")
        
#     except Exception as e:
#         print("\n" + "="*60)
#         print("❌ 下载失败")
#         print("="*60)
#         print(f"错误信息: {e}")
#         print("\n💡 解决方案:")
#         print("1. 检查网络连接")
#         print("2. 尝试使用 VPN 或代理")
#         print("3. 手动从浏览器下载:")
#         print("   访问: https://hf-mirror.com/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
#         print("   下载所有文件到: backend/models/paraphrase-multilingual-MiniLM-L12-v2/")
#         print("="*60)
#         sys.exit(1)

# if __name__ == '__main__':
#     download_model()

# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure

# try:
#     # 尝试连接到 MongoDB
#     client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    
#     # 测试连接
#     client.admin.command('ping')
#     print("MongoDB 连接成功!")
    
# except ConnectionFailure:
#     print("MongoDB 连接失败!")
# except Exception as e:
#     print(f"连接出现错误: {e}")
# databases = client.list_database_names()
# print("所有数据库:", databases)


# test_mongodb.查看数据库
# from pymongo import MongoClient
# from config import Config

# try:
#     print(f"🔍 正在连接 MongoDB: {Config.MONGODB_URI}")
#     client = MongoClient(Config.MONGODB_URI)
    
#     # 测试连接
#     result = client.admin.command('ping')
#     print("✅ MongoDB 连接成功！")
#     print(f"   响应: {result}")
    
#     # 检查数据库
#     db = client[Config.DATABASE_NAME]
#     print(f"\n📊 数据库 '{Config.DATABASE_NAME}' 信息:")
    
#     # 检查集合
#     collections = db.list_collection_names()
#     print(f"   集合数量: {len(collections)}")
#     for col_name in collections:
#         col = db[col_name]
#         count = col.count_documents({})
#         print(f"   - {col_name}: {count} 条记录")
    
#     # 检查缓存集合
#     if 'analysis_cache' in collections:
#         cache_col = db['analysis_cache']
#         cache_count = cache_col.count_documents({})
#         print(f"\n💾 缓存统计:")
#         print(f"   总缓存数: {cache_count}")
        
#         # 按模型统计
#         for model in ['gemini', 'gpt4o']:
#             model_count = cache_col.count_documents({"model": model})
#             print(f"   - {model}: {model_count} 条")
    
#     client.close()
    
# except Exception as e:
#     print(f"❌ MongoDB 连接失败: {e}")
#     print("\n💡 可能的原因:")
#     print("1. MongoDB 服务未启动")
#     print("2. MongoDB 连接地址不正确")
#     print("3. 防火墙阻止了连接")
#     print("\n💡 解决方案:")
#     print("1. 检查 MongoDB 是否运行: 查看任务管理器或服务")
#     print("2. 启动 MongoDB 服务")
#     print("3. 检查连接地址是否正确")







"""
交互式删除 analysis_cache 集合中的记录
逐条展示，询问是否删除
"""
from pymongo import MongoClient
from config import Config
import sys
from datetime import datetime

def format_datetime(dt):
    """格式化日期时间"""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def clear_cache_interactive():
    """交互式删除记录"""
    try:  # 添加 try 语句
        print("="*70)
        print("🗑️  交互式删除 analysis_cache 集合记录")
        print("="*70)
        
        # 连接 MongoDB
        client = MongoClient(Config.MONGODB_URI)
        db = client[Config.DATABASE_NAME]
        cache_collection = db.analysis_cache
        
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB 连接成功\n")
        
        # 获取所有记录
        all_records = list(cache_collection.find({}))
        total_count = len(all_records)
        
        if total_count == 0:
            print("ℹ️  集合中没有任何记录")
            client.close()
            return
        
        print(f"📊 找到 {total_count} 条记录\n")
        print("="*70)
        
        deleted_count = 0
        kept_count = 0
        
        # 逐条展示并询问
        for i, record in enumerate(all_records, 1):
            print(f"\n📄 记录 {i}/{total_count}")
            print("-" * 70)
            
            # 提取记录信息
            record_id = record.get('_id')
            image_hash = record.get('image_hash', 'N/A')
            model = record.get('model', 'N/A')
            created_at = record.get('created_at', 'N/A')
            updated_at = record.get('updated_at', 'N/A')
            result = record.get('result', {})
            
            # 显示记录详情
            print(f"记录 ID: {record_id}")
            print(f"图片哈希: {image_hash[:32]}..." if len(str(image_hash)) > 32 else f"图片哈希: {image_hash}")
            print(f"模型: {model}")
            print(f"创建时间: {format_datetime(created_at)}")
            print(f"更新时间: {format_datetime(updated_at)}")
            
            # 显示结果信息
            if result:
                hazard_type = result.get('type', 'N/A')
                description = result.get('description', 'N/A')
                confidence = result.get('confidence', 'N/A')
                bert_sim = result.get('bert_similarity', 'N/A')
                tfidf_sim = result.get('tfidf_similarity', 'N/A')
                
                print(f"\n分析结果:")
                print(f"  隐患类型: {hazard_type}")
                print(f"  置信度: {confidence}")
                print(f"  BERT相似度: {bert_sim}")
                print(f"  TF-IDF相似度: {tfidf_sim}")
                
                # 显示描述（截断）
                if description != 'N/A' and len(str(description)) > 100:
                    print(f"  描述: {str(description)[:100]}...")
                else:
                    print(f"  描述: {description}")
            
            print("-" * 70)
            
            # 询问是否删除
            while True:
                choice = input(f"\n❓ 是否删除这条记录？(y/n/q退出): ").strip().lower()
                
                if choice == 'y' or choice == 'yes' or choice == '是':
                    # 删除记录
                    delete_result = cache_collection.delete_one({"_id": record_id})
                    if delete_result.deleted_count > 0:
                        print(f"✅ 已删除记录 {i}")
                        deleted_count += 1
                    else:
                        print(f"⚠️  删除失败（记录可能已被删除）")
                    break
                    
                elif choice == 'n' or choice == 'no' or choice == '否':
                    print(f"⏭️  跳过记录 {i}")
                    kept_count += 1
                    break
                    
                elif choice == 'q' or choice == 'quit' or choice == '退出':
                    print(f"\n🛑 用户取消操作")
                    print(f"📊 统计: 已删除 {deleted_count} 条，保留 {kept_count} 条，剩余 {total_count - i} 条未处理")
                    client.close()
                    return
                    
                else:
                    print("⚠️  请输入 y(是)/n(否)/q(退出)")
        
        # 显示最终统计
        print("\n" + "="*70)
        print("📊 删除完成统计")
        print("="*70)
        print(f"✅ 已删除: {deleted_count} 条")
        print(f"⏭️  已保留: {kept_count} 条")
        
        # 验证剩余记录数
        remaining = cache_collection.count_documents({})
        print(f"📋 剩余记录数: {remaining}")
        print("="*70)
        
        client.close()
        
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    clear_cache_interactive()