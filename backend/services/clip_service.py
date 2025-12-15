import torch
import clip
import numpy as np
import random
from pymongo import MongoClient
from config import Config

class CLIPService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {self.device}")
        
        try:
            self.model, self.preprocess = clip.load(Config.CLIP_MODEL_NAME, device=self.device)
            print("CLIP模型加载成功")
        except Exception as e:
            print(f"CLIP模型加载失败: {e}")
            raise e
            
        try:
            self.db = MongoClient(Config.MONGODB_URI)[Config.DATABASE_NAME]
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise e
        
        # 预编码所有隐患类别的文本描述
        self.hazard_descriptions = self._load_hazard_descriptions()
        self.text_features = self._encode_hazard_descriptions()
        
    def _load_hazard_descriptions(self):
        """加载隐患类别描述"""
        descriptions = {
            "1": "未按规定穿戴反光安全服",
            "2": "高处作业未正确使用安全带",
            "3": "配电箱未及时锁闭",
            "4": "未按规定配置灭火器、消防设施等",
            "5": "现场防护栏等安全防护设施缺失、破损或设置不规范",
            "6": "设备安全防护设施、装置缺失或失效",
            "7": "起重吊装设备钢丝绳磨损、断丝严重，搭接长度不足",
            "8": "汽车吊、随车吊、泵车支腿未全部伸出、未垫枕木进行作业",
            "9": "基坑支护措施不到位",
            "10": "灭火器未按规定要求放置",
            "11": "未按规定设置接地线或接地不良",
            "12": "安全警示标志标识缺失或设置不规范",
            "13": "灭火器压力不足，灭火器、消防设施等未按规定进行检查、维护",
            "14": "不符合三级配电两级漏电保护、一机一闸一漏一箱要求",
            "15": "电缆外皮破损或敷设不规范"
        }
        return descriptions
    
    def _encode_hazard_descriptions(self):
        """预编码所有隐患描述文本"""
        text_descriptions = list(self.hazard_descriptions.values())
        text_tokens = clip.tokenize(text_descriptions).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return text_features
    
    def classify_hazard(self, image):
        """直接分类隐患类型（零样本学习）"""
        try:
            image_features = self.encode_image(image)
            
            # 计算与所有文本描述的相似度
            similarities = torch.cosine_similarity(image_features, self.text_features)
            
            # 获取最相似的类别
            best_match_idx = similarities.argmax().item()
            confidence = similarities[best_match_idx].item()
            
            hazard_type = str(best_match_idx + 1)
            description = self.hazard_descriptions[hazard_type]
            
            return {
                'type': hazard_type,
                'description': description,
                'confidence': confidence,
                'all_scores': {
                    str(i+1): score.item() 
                    for i, score in enumerate(similarities)
                }
            }
        except Exception as e:
            print(f"CLIP分类失败: {e}")
            return {
                'type': 'unknown',
                'description': f'分类失败: {e}',
                'confidence': 0.0,
                'all_scores': {}
            }
        
    def encode_image(self, image):
        """将图片编码为特征向量"""
        try:
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            return image_features  # 直接返回Tensor，不转换为numpy
        except Exception as e:
            raise Exception(f"图片编码失败: {e}")
    
    def find_similar_cases(self, image, top_k=5):
        """查找最相似的历史案例"""
        try:
            query_features = self.encode_image(image)
            # 确保query_features在CPU上并转换为numpy数组
            if query_features.is_cuda:
                query_features_np = query_features.cpu().numpy()
            else:
                query_features_np = query_features.numpy()
            
            # 从数据库获取所有案例的特征向量
            cases = list(self.db.cases.find({}, {'features': 1, 'description': 1, 'type': 1, 'category_description': 1}))
            
            if not cases:
                print("数据库中没有案例数据")
                return []
            
            similarities = []
            for case in cases:
                if 'features' in case:
                    case_features = np.array(case['features'])
                    similarity = np.dot(query_features_np, case_features.T).item()
                    similarities.append((similarity, case))
            
            # 按相似度排序并返回前k个
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [case for _, case in similarities[:top_k]]
            
        except Exception as e:
            print(f"查找相似案例失败: {e}")
            return []
    
    def get_random_examples(self, count=3):
        """随机选择few-shot示例"""
        try:
            all_cases = list(self.db.cases.find({}, {'description': 1, 'type': 1, 'suggestion': 1, 'category_description': 1}))
            if not all_cases:
                return []
            return random.sample(all_cases, min(count, len(all_cases)))
        except Exception as e:
            print(f"获取随机示例失败: {e}")
            return []