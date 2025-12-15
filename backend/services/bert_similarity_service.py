import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Tuple
from config import Config

# 配置 Hugging Face 镜像源（如果在中国大陆，可以使用镜像）
# 如果遇到 SSL 错误或连接问题，取消下面的注释来使用镜像源
#os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 使用 Hugging Face 镜像


class BertSimilarityService:
    """BERT语义相似度计算服务"""
    
    def __init__(self):
        # 使用中文BERT模型
        print("🔄 正在加载BERT模型...")
        
        # 首先检查是否有本地模型
        local_model_paths = [
            './models/paraphrase-multilingual-MiniLM-L12-v2',
            './models/distiluse-base-multilingual-cased-v1',
            os.path.expanduser('~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2'),
        ]
        
        # 模型加载策略：按优先级尝试多个模型
        # 先尝试本地路径，再尝试在线下载
        model_candidates = []
        
        # 添加本地模型路径
        for local_path in local_model_paths:
            if os.path.exists(local_path):
                model_candidates.append(local_path)
                print(f"📁 发现本地模型: {local_path}")
        
        # 添加在线模型（如果本地没有）
        if not model_candidates:
            model_candidates.extend([
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                'paraphrase-multilingual-MiniLM-L12-v2',
                'sentence-transformers/distiluse-base-multilingual-cased-v1',
                'distiluse-base-multilingual-cased-v1',
            ])
        
        self.model = None
        last_error = None
        
        for model_name in model_candidates:
            try:
                print(f"🔄 尝试加载模型: {model_name}")
                self.model = SentenceTransformer(model_name)
                print(f"✅ 成功加载模型: {model_name}")
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(f"⚠️  模型 {model_name} 加载失败: {error_msg[:100]}...")
                
                # 如果是 SSL 错误，给出特殊提示
                if 'SSL' in error_msg or 'SSLError' in error_msg:
                    print("💡 提示: 检测到 SSL 连接错误，可能是网络问题。")
                    print("   解决方案:")
                    print("   1. 检查网络连接")
                    print("   2. 如果在中国大陆，可以配置镜像源:")
                    print("      在代码中取消注释: os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'")
                    print("   3. 或手动下载模型到本地")
                continue
        
        if self.model is None:
            error_msg = f"❌ 所有模型加载都失败了。最后一个错误: {last_error}"
            print(error_msg)
            print("\n" + "="*60)
            print("💡 解决方案建议:")
            print("="*60)
            print("1. 检查网络连接，确认能否访问 https://hf-mirror.com")
            print("2. 如果网络受限，可以:")
            print("   - 使用 VPN 或代理")
            print("   - 手动下载模型到本地（推荐）")
            print("   - 临时禁用 SSL 验证（不安全，仅用于测试）")
            print("3. 手动下载模型步骤:")
            print("   a) 访问: https://hf-mirror.com/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            print("   b) 下载所有文件到本地目录")
            print("   c) 修改代码使用本地路径: SentenceTransformer('./models/paraphrase-multilingual-MiniLM-L12-v2')")
            print("="*60)
            
            # 询问是否继续运行（如果 BERT 不是必需的）
            print("\n⚠️  警告: 程序无法继续运行，因为 BERT 模型是必需的。")
            raise RuntimeError(
                "无法加载 BERT 模型。请检查网络连接，或手动下载模型到本地。\n"
                "详细解决方案请查看上方的提示信息。"
            )
        
        print("✅ BERT模型加载完成")
        
        # 加载隐患类别描述
        self.hazard_descriptions = self._load_hazard_descriptions()
        # 预编码所有类别描述
        self.description_embeddings = self._encode_descriptions()
    
    def _load_hazard_descriptions(self) -> Dict[str, str]:
        """加载隐患类别描述文档"""
        descriptions = {}
        description_file = Config.CATEGORY_FILE
        
        try:
            if os.path.exists(description_file):
                with open(description_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line and line:
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                hazard_type = parts[0].strip()
                                description = parts[1].strip()
                                if description:
                                    descriptions[hazard_type] = description
                print(f"✅ 加载了 {len(descriptions)} 个隐患类别描述")
            else:
                print(f"⚠️  描述文件不存在: {description_file}")
        except Exception as e:
            print(f"❌ 加载描述文件失败: {e}")
        
        return descriptions
    
    def _encode_descriptions(self) -> Dict[str, np.ndarray]:
        """预编码所有隐患类别描述"""
        embeddings = {}
        description_texts = []
        type_keys = []
        
        for hazard_type, description in self.hazard_descriptions.items():
            description_texts.append(description)
            type_keys.append(hazard_type)
        
        if description_texts:
            # 批量编码提高效率
            encoded = self.model.encode(description_texts, convert_to_numpy=True)
            for i, hazard_type in enumerate(type_keys):
                embeddings[hazard_type] = encoded[i]
        
        return embeddings
    
    def calculate_similarity(
        self, 
        generated_description: str, 
        hazard_type: str
    ) -> Tuple[float, str]:
        """
        计算生成的描述与对应类型标准描述的相似度
        
        Args:
            generated_description: 大模型生成的隐患描述
            hazard_type: 隐患类型（如 "1", "2"）
        
        Returns:
            (相似度分数, 标准描述文本)
        """
        try:
            # 获取标准描述
            standard_description = self.hazard_descriptions.get(hazard_type)
            if not standard_description:
                print(f"⚠️  未找到类型 {hazard_type} 的标准描述")
                return 0.0, ""
            
            # 编码生成的描述
            generated_embedding = self.model.encode(
                [generated_description], 
                convert_to_numpy=True
            )[0]
            
            # 获取预编码的标准描述
            standard_embedding = self.description_embeddings.get(hazard_type)
            if standard_embedding is None:
                # 如果预编码中没有，实时编码
                standard_embedding = self.model.encode(
                    [standard_description], 
                    convert_to_numpy=True
                )[0]
            
            # 计算余弦相似度
            similarity = cosine_similarity(
                generated_embedding.reshape(1, -1),
                standard_embedding.reshape(1, -1)
            )[0][0]
            
            # 确保相似度在 [0, 1] 范围内
            similarity = max(0.0, min(1.0, float(similarity)))
            
            return similarity, standard_description
            
        except Exception as e:
            print(f"❌ 计算相似度失败: {e}")
            return 0.0, ""
    
    def get_average_similarity(self) -> Dict[str, float]:
        """获取所有已识别图像的平均相似度"""
        from pymongo import MongoClient
        from config import Config
        
        try:
            client = MongoClient(Config.MONGODB_URI)
            db = client[Config.DATABASE_NAME]
            cache_collection = db.analysis_cache
            
            # 获取所有有相似度记录的结果
            all_results = list(cache_collection.find(
                {"result.bert_similarity": {"$exists": True}}
            ))
            
            if not all_results:
                return {
                    "average": 0.0,
                    "count": 0,
                    "by_model": {}
                }
            
            # 计算总体平均
            similarities = [
                r["result"].get("bert_similarity", 0.0) 
                for r in all_results
            ]
            average = sum(similarities) / len(similarities) if similarities else 0.0
            
            # 按模型分组计算
            by_model = {}
            for model in ['gemini', 'gpt4o']:
                model_results = [
                    r["result"].get("bert_similarity", 0.0)
                    for r in all_results
                    if r.get("model") == model and r["result"].get("bert_similarity")
                ]
                if model_results:
                    by_model[model] = sum(model_results) / len(model_results)
                else:
                    by_model[model] = 0.0
            
            return {
                "average": average,
                "count": len(all_results),
                "by_model": by_model
            }
        except Exception as e:
            print(f"❌ 获取平均相似度失败: {e}")
            return {
                "average": 0.0,
                "count": 0,
                "by_model": {}
            }