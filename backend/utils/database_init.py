import os
import json
import re
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from config import Config
from services.clip_service import CLIPService
from utils.image_processor import ImageProcessor

def init_database():
    """初始化数据库和索引"""
    try:
        # 连接MongoDB
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB连接成功")
        
        db = client[Config.DATABASE_NAME]
        
        # 创建集合
        cases_collection = db.cases
        
        # 删除现有索引（如果需要重新创建）
        # cases_collection.drop_indexes()
        
        # 创建索引
        cases_collection.create_index("type")
        cases_collection.create_index("filename")
        cases_collection.create_index("image_id")
        cases_collection.create_index([("type", 1), ("image_id", 1)], unique=True)
        
        # 创建文本搜索索引
        cases_collection.create_index([
            ("description", "text"),
            ("category_description", "text")
        ])
        
        print("✅ 数据库索引创建完成")
        
        # 显示数据库统计信息
        stats = db.command("collStats", "cases")
        print(f"📊 当前cases集合文档数量: {stats.get('count', 0)}")
        
        return db
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB连接失败: {e}")
        print("请确保MongoDB服务正在运行")
        return None
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return None

def load_hazard_descriptions():
    """加载隐患描述文档"""
    description_file = "datasets/隐患数据集/隐患数据集/隐患描述文档.txt"
    category_file = "datasets/隐患数据集/隐患数据集/隐患类别描述文档.txt"
    
    descriptions = {}
    categories = {}
    
    # 加载类别描述
    try:
        if os.path.exists(category_file):
            with open(category_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if ':' in line and line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            category_id = parts[0].strip()
                            category_desc = parts[1].strip()
                            if category_desc:  # 确保描述不为空
                                categories[category_id] = category_desc
            print(f"✅ 加载了 {len(categories)} 个隐患类别")
        else:
            print(f"⚠️  类别描述文件不存在: {category_file}")
    except Exception as e:
        print(f"❌ 加载类别描述失败: {e}")
    
    # 加载详细描述
    try:
        if os.path.exists(description_file):
            with open(description_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if '-' in line and ':' in line and line:
                        # 解析格式: 1-1:描述内容
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            image_key = parts[0].strip()
                            description = parts[1].strip()
                            if description:  # 确保描述不为空
                                descriptions[image_key] = description
            print(f"✅ 加载了 {len(descriptions)} 个详细描述")
        else:
            print(f"⚠️  详细描述文件不存在: {description_file}")
    except Exception as e:
        print(f"❌ 加载详细描述失败: {e}")
    
    return descriptions, categories

def load_dataset():
    """加载数据集到数据库"""
    # 初始化数据库
    db = init_database()
    if db is None:
        return
    try:
        # 加载描述文档
        descriptions, categories = load_hazard_descriptions()
        
        # 初始化服务
        print("🔄 正在初始化CLIP服务...")
        clip_service = CLIPService()
        image_processor = ImageProcessor()
        
        # 图片文件夹路径
        image_folder = "datasets/隐患数据集/隐患数据集/隐患图片"
        
        if not os.path.exists(image_folder):
            print(f"❌ 图片文件夹不存在: {image_folder}")
            return
        
        # 获取所有图片文件
        image_files = [f for f in os.listdir(image_folder) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'))]
        
        print(f"📁 找到 {len(image_files)} 个图片文件")
        
        loaded_count = 0
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, filename in enumerate(image_files, 1):
            try:
                print(f"🔄 处理进度: {i}/{len(image_files)} - {filename}")
                
                # 解析文件名获取类型和编号
                name_without_ext = os.path.splitext(filename)[0]
                parts = name_without_ext.split('-')
                
                if len(parts) >= 2:
                    hazard_type = parts[0]
                    image_id = parts[1]
                    
                    image_path = os.path.join(image_folder, filename)
                    
                    # 验证图片文件
                    if not image_processor.validate_image(image_path):
                        print(f"⚠️  无效图片文件: {filename}")
                        error_count += 1
                        continue
                    
                    # 处理图片
                    processed_image = image_processor.process_image(image_path)
                    
                    # 提取特征向量
                    features = clip_service.encode_image(processed_image)
                    
                    # 构建描述键（格式: 1-1）
                    desc_key = f"{hazard_type}-{image_id}"
                    description = descriptions.get(desc_key, f"隐患类型{hazard_type}的示例图片")
                    category_desc = categories.get(hazard_type, f"隐患类型{hazard_type}")
                    
                    # 存储到数据库
                    case_data = {
                        'filename': filename,
                        'type': hazard_type,
                        'image_id': image_id,
                        'features': features.tolist(),
                        'description': description,
                        'category_description': category_desc,
                        'suggestion': generate_suggestion(hazard_type, category_desc),
                        'image_path': image_path,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'file_size': os.path.getsize(image_path),
                        'file_type': os.path.splitext(filename)[1].lower()
                    }
                    
                    # 检查是否已存在
                    existing = db.cases.find_one({'filename': filename})
                    if existing:
                        # 更新现有记录
                        case_data['created_at'] = existing.get('created_at', datetime.now())
                        db.cases.update_one(
                            {'filename': filename}, 
                            {'$set': case_data}
                        )
                        updated_count += 1
                        print(f"🔄 已更新: {filename}")
                    else:
                        # 插入新记录
                        db.cases.insert_one(case_data)
                        loaded_count += 1
                        print(f"✅ 已加载: {filename}")
                    
                else:
                    print(f"⚠️  文件名格式不正确: {filename}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ 处理文件 {filename} 时出错: {str(e)}")
                error_count += 1
        
        # 显示统计结果
        print(f"\n📊 数据集加载完成:")
        print(f"✅ 成功加载: {loaded_count} 个文件")
        print(f"🔄 更新文件: {updated_count} 个文件")
        print(f"❌ 错误文件: {error_count} 个文件")
        
        # 显示数据库统计
        total_docs = db.cases.count_documents({})
        print(f"📈 数据库中总文档数: {total_docs}")
        
        # 按类型统计
        pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        type_stats = list(db.cases.aggregate(pipeline))
        print("📋 按类型统计:")
        for stat in type_stats:
            print(f"   类型 {stat['_id']}: {stat['count']} 个文件")
            
    except Exception as e:
        print(f"❌ 数据集加载失败: {e}")

def generate_suggestion(hazard_type, category_desc):
    """根据隐患类型生成整改建议"""
    suggestions = {
        "1": "立即停止作业，要求所有人员按规定穿戴反光安全服和安全帽，并进行安全教育培训",
        "2": "立即停止高空作业，要求作业人员正确佩戴安全带，并设置水平安全绳等防护措施",
        "3": "立即关闭配电箱并上锁，检查配电箱防护设施，确保符合安全规范",
        "4": "立即配置符合要求的灭火器和消防设施，并定期检查维护",
        "5": "立即修复或重新设置防护栏等安全防护设施，确保其完整有效",
        "6": "立即修复或更换设备安全防护设施，确保所有防护装置正常工作",
        "7": "立即更换磨损严重的钢丝绳，确保搭接长度符合规范要求",
        "8": "立即调整支腿使其全部伸出并垫好枕木，确保设备稳定作业",
        "9": "立即完善基坑支护措施，确保基坑安全稳定",
        "10": "立即将灭火器按规定要求放置，并定期检查维护",
        "11": "立即设置或修复接地线，确保接地良好",
        "12": "立即补充缺失的安全警示标志，并规范设置位置",
        "13": "立即更换压力不足的灭火器，建立定期检查维护制度",
        "14": "立即整改配电系统，确保符合三级配电两级漏电保护要求",
        "15": "立即修复破损电缆，规范电缆敷设，确保用电安全"
    }
    
    return suggestions.get(hazard_type, f"针对{category_desc}，请立即整改相关安全隐患，确保符合安全规范要求")

def cleanup_database():
    """清理数据库（可选功能）"""
    try:
        db = init_database()
        if db is not None:
            result = db.cases.delete_many({})
            print(f"🗑️  已清理 {result.deleted_count} 个文档")
    except Exception as e:
        print(f"❌ 清理数据库失败: {e}")

def backup_database():
    """备份数据库"""
    try:
        import shutil
        from datetime import datetime
        
        backup_dir = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 这里可以添加备份逻辑
        print(f"📦 备份已保存到: {backup_dir}")
    except Exception as e:
        print(f"❌ 备份失败: {e}")

if __name__ == "__main__":
    print("🚀 开始初始化MongoDB数据库...")
    
    # 可选：清理现有数据
    # cleanup_database()
    
    # 初始化并加载数据
    load_dataset()
    
    print("🎉 数据库初始化完成！")