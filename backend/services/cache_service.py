import hashlib
from pymongo import MongoClient
from datetime import datetime
from config import Config
from typing import Optional, Dict
import os

class CacheService:
    """分析结果缓存服务"""
    
    def __init__(self):
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.DATABASE_NAME]
            self.cache_collection = self.db.analysis_cache
            
            # 删除旧的错误索引（如果存在）
            try:
                self.cache_collection.drop_index("image_hash_1")
            except:
                pass
            
            # 创建复合唯一索引（image_hash + model）
            # 这样同一个图片的不同模型结果可以共存
            self.cache_collection.create_index(
                [("image_hash", 1), ("model", 1)], 
                unique=True,
                name="image_hash_model_idx"
            )
            self.cache_collection.create_index("created_at")
            
            # 测试连接
            self.client.admin.command('ping')
            print("✅ MongoDB 连接成功，缓存服务已初始化")
        except Exception as e:
            print(f"❌ MongoDB 连接失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def calculate_image_hash(self, image_path: str) -> str:
        """计算图片的MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            hash_value = hash_md5.hexdigest()
            print(f"🔍 计算图片哈希: {hash_value[:8]}... (文件: {os.path.basename(image_path)})")
            return hash_value
        except Exception as e:
            print(f"❌ 计算哈希失败: {e}")
            raise
    
    def calculate_bytes_hash(self, image_bytes: bytes) -> str:
        """计算图片字节流的MD5哈希值"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def get_cached_result(self, image_hash: str, model: str) -> Optional[Dict]:
        """从缓存中获取分析结果"""
        try:
            print(f"🔍 查询缓存: hash={image_hash[:8]}..., model={model}")
            
            cached = self.cache_collection.find_one({
                "image_hash": image_hash,
                "model": model
            })
            
            if cached:
                result = {
                    "image_hash": cached.get("image_hash"),
                    "model": cached.get("model"),
                    "result": cached.get("result"),
                    "created_at": cached.get("created_at"),
                    "updated_at": cached.get("updated_at"),
                }
                print(f"✅ 从缓存中获取结果 (hash: {image_hash[:8]}..., model: {model})")
                return result
            
            print(f"⚠️  缓存未命中 (hash: {image_hash[:8]}..., model: {model})")
            return None
        except Exception as e:
            print(f"❌ 查询缓存失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_result(self, image_hash: str, result: Dict, model: str) -> bool:
        """保存分析结果到缓存"""
        try:
            print(f"💾 开始保存到缓存: hash={image_hash[:8]}..., model={model}")
            
            # 验证结果数据
            if not result:
                print("❌ 结果数据为空，无法保存")
                return False
            
            cache_data = {
                "image_hash": image_hash,
                "model": model,
                "result": result,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            
            # 使用 upsert 更新或插入
            update_result = self.cache_collection.update_one(
                {"image_hash": image_hash, "model": model},
                {"$set": cache_data},
                upsert=True
            )
            
            if update_result.upserted_id:
                print(f"✅ 已插入新缓存记录 (hash: {image_hash[:8]}..., model: {model}, _id: {update_result.upserted_id})")
            elif update_result.modified_count > 0:
                print(f"✅ 已更新缓存记录 (hash: {image_hash[:8]}..., model: {model})")
            else:
                print(f"⚠️  缓存记录未变化 (hash: {image_hash[:8]}..., model: {model})")
            
            # 验证保存是否成功
            verify = self.cache_collection.find_one({
                "image_hash": image_hash,
                "model": model
            })
            
            if verify:
                print(f"✅ 验证成功：缓存已保存到数据库")
                return True
            else:
                print(f"❌ 验证失败：缓存未找到")
                return False
                
        except Exception as e:
            print(f"❌ 保存缓存失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        try:
            total = self.cache_collection.count_documents({})
            by_model = {}
            for model in ['gemini', 'gpt4o']:
                count = self.cache_collection.count_documents({"model": model})
                by_model[model] = count
            return {
                "total": total,
                "by_model": by_model
            }
        except Exception as e:
            print(f"⚠️  获取缓存统计失败: {e}")
            return {"total": 0, "by_model": {}}