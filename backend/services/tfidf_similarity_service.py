import os
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Tuple
from config import Config


class TfidfSimilarityService:
    """TF-IDF文本相似度计算服务"""
    
    def __init__(self):
        # 加载隐患类别描述
        self.hazard_descriptions = self._load_hazard_descriptions()
        # 初始化 TF-IDF 向量化器
        self.vectorizer = self._init_vectorizer()
        print("✅ TF-IDF 相似度服务初始化完成")
    
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
                print(f"✅ 加载了 {len(descriptions)} 个隐患类别描述（TF-IDF）")
            else:
                print(f"⚠️  描述文件不存在: {description_file}")
        except Exception as e:
            print(f"❌ 加载描述文件失败: {e}")
        
        return descriptions
    
    def _init_vectorizer(self) -> TfidfVectorizer:
        """初始化 TF-IDF 向量化器"""
        # 准备所有描述文本用于训练向量化器
        all_descriptions = list(self.hazard_descriptions.values())
        
        if not all_descriptions:
            print("⚠️  没有描述文本，使用默认向量化器")
            return TfidfVectorizer(
                analyzer='char',  # 使用字符级别（适合中文）
                ngram_range=(1, 2),  # 1-gram 和 2-gram
                max_features=5000
            )
        
        # 使用中文分词
        def tokenizer(text):
            return list(jieba.cut(text))
        
        vectorizer = TfidfVectorizer(
            tokenizer=tokenizer,
            token_pattern=None,  # 使用自定义分词器
            ngram_range=(1, 2),  # 1-gram 和 2-gram
            max_features=5000,
            min_df=1,
            max_df=0.95
        )
        
        # 训练向量化器
        try:
            vectorizer.fit(all_descriptions)
            print(f"✅ TF-IDF 向量化器训练完成（词汇表大小: {len(vectorizer.vocabulary_)}）")
        except Exception as e:
            print(f"⚠️  TF-IDF 训练失败，使用字符级别: {e}")
            # 回退到字符级别
            vectorizer = TfidfVectorizer(
                analyzer='char',
                ngram_range=(1, 2),
                max_features=5000
            )
            vectorizer.fit(all_descriptions)
        
        return vectorizer
    
    def calculate_similarity(
        self, 
        generated_description: str, 
        hazard_type: str
    ) -> Tuple[float, str]:
        """
        计算生成的描述与对应类型标准描述的 TF-IDF 相似度
        
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
            
            # 向量化两个文本
            try:
                vectors = self.vectorizer.transform([generated_description, standard_description])
            except Exception as e:
                print(f"⚠️  向量化失败: {e}，使用字符级别重试")
                # 如果分词失败，使用字符级别
                char_vectorizer = TfidfVectorizer(
                    analyzer='char',
                    ngram_range=(1, 2),
                    max_features=5000
                )
                vectors = char_vectorizer.fit_transform([generated_description, standard_description])
            
            # 计算余弦相似度
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            # 确保相似度在 [0, 1] 范围内
            similarity = max(0.0, min(1.0, float(similarity)))
            
            return similarity, standard_description
            
        except Exception as e:
            print(f"❌ 计算 TF-IDF 相似度失败: {e}")
            import traceback
            traceback.print_exc()
            return 0.0, ""