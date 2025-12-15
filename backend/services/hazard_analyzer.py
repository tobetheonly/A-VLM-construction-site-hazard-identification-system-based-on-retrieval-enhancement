import os
import json
import base64
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from services.tfidf_similarity_service import TfidfSimilarityService
from services.clip_service import CLIPService
from services.llm_service import LLMService
from services.bert_similarity_service import BertSimilarityService
from utils.image_processor import ImageProcessor
from config import Config


class HazardAnalyzer:
    """隐患分析器 - 整合CLIP模型、LLM服务和相似案例检索"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.clip_service = CLIPService()
        self.image_processor = ImageProcessor()
        self.bert_similarity = BertSimilarityService()  # 初始化BERT相似度服务
        self.tfidf_similarity = TfidfSimilarityService()

        # 隐患类型映射
        self.hazard_types = {
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
            "15": "电缆外皮破损或敷设不规范",
        }

    def analyze_hazard(
        self,
        image_path: str,
        top_k: int = 5,
        few_shot_count: int = 3,
        provider: str = "gemini",
    ) -> Dict:
        """分析隐患图片，可指定 provider=gemini/gpt4o"""
        try:
            print(f"🔍 开始分析图片: {image_path}")

            # 1. 处理图片
            processed_image = self.image_processor.process_image(image_path)

            # 2. CLIP 直接分类
            direct_classification = self.clip_service.classify_hazard(processed_image)
            print(
                f"✅ CLIP直接分类结果: 类型 {direct_classification['type']}, 置信度 {direct_classification['confidence']:.3f}"
            )

            # 3. 检索相似案例
            similar_cases = self.clip_service.find_similar_cases(
                processed_image, top_k=top_k
            )
            print(f"📋 找到 {len(similar_cases)} 个相似案例")

            # 4. Few-shot 示例
            few_shot_examples = self.clip_service.get_random_examples(
                count=few_shot_count
            )
            print(f"🎯 获取 {len(few_shot_examples)} 个Few-shot示例")

            # 5. 图片转 base64
            image_base64 = self.image_processor.image_to_base64(processed_image)

            # 6. 调用 LLM（可切换模型）
            enhanced_result = self.llm_service.generate_hazard_analysis(
                image_base64=image_base64,
                similar_cases=similar_cases,
                few_shot_examples=few_shot_examples,
                provider=provider,
            )
            print("#####################llm输出结果########################")
            print(enhanced_result)
            
            # 清理 markdown 代码块标记
            cleaned_result = enhanced_result.strip()
            # 删除 ```json 或 ``` 开头的标记
            cleaned_result = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_result)
            # 删除结尾的 ``` 标记
            cleaned_result = re.sub(r'\n?```\s*$', '', cleaned_result)
            cleaned_result = cleaned_result.strip()
            
            print("#####################清理后的llm输出结果########################")
            print(cleaned_result)

            # 7. 整合结果（带上 model）
            final_result = self._integrate_results(
                direct_classification=direct_classification,
                enhanced_result=cleaned_result,
                similar_cases=similar_cases,
                model=provider,
            )

            print(
                f"🎉 分析完成: 类型 {final_result['type']}, 置信度 {final_result['confidence']:.3f}, BERT相似度 {final_result.get('bert_similarity', 0.0):.4f}"
            )
            return final_result

        except Exception as e:
            print(f"❌ 隐患分析失败: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e), model=provider)

    def _integrate_results(
        self,
        direct_classification: Dict,
        enhanced_result: str,
        similar_cases: List,
        model: str,
    ) -> Dict:
        """整合直接分类和增强分析结果"""
        try:
            enhanced_data = None
            
            # 处理字符串类型的 enhanced_result
            if isinstance(enhanced_result, str):
                try:
                    enhanced_data = json.loads(enhanced_result)
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON解析失败: {e}")
                    print(f"原始内容: {enhanced_result[:200]}...")
                    enhanced_data = None
            else:
                enhanced_data = enhanced_result

            if enhanced_data and isinstance(enhanced_data, Dict):
                result = {
                    "id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": enhanced_data.get("type", direct_classification["type"]),
                    "description": enhanced_data.get(
                        "description", direct_classification["description"]
                    ),
                    "suggestion": enhanced_data.get(
                        "suggestion",
                        self._get_default_suggestion(direct_classification["type"]),
                    ),
                    "confidence": enhanced_data.get(
                        "confidence", direct_classification["confidence"]
                    ),
                    "similar_cases": [
                        case.get("description", "") for case in similar_cases[:3]
                    ],
                    "analysis_method": "CLIP + LLM Enhanced",
                    "model": model,
                    "created_at": datetime.now().isoformat(),
                }
            else:
                result = {
                    "id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": direct_classification["type"],
                    "description": direct_classification["description"],
                    "suggestion": self._get_default_suggestion(
                        direct_classification["type"]
                    ),
                    "confidence": direct_classification["confidence"],
                    "similar_cases": [
                        case.get("description", "") for case in similar_cases[:3]
                    ],
                    "analysis_method": "CLIP Direct Classification",
                    "model": model,
                    "created_at": datetime.now().isoformat(),
                }

            # 计算BERT相似度（对所有结果都计算）
            hazard_type = result["type"]
            generated_desc = result["description"]
            
            try:
                similarity, standard_desc = self.bert_similarity.calculate_similarity(
                    generated_desc, hazard_type
                )
                result["bert_similarity"] = similarity
                result["standard_description"] = standard_desc
                print(f"📊 BERT相似度: {similarity:.4f} (类型 {hazard_type})")
            except Exception as e:
                print(f"⚠️  计算BERT相似度失败: {e}")
                result["bert_similarity"] = 0.0
                result["standard_description"] = ""
            # 添加 TF-IDF 相似度计算
            try:
                tfidf_sim, _ = self.tfidf_similarity.calculate_similarity(
                    generated_desc, hazard_type
                )
                result["tfidf_similarity"] = tfidf_sim
                print(f"📊 TF-IDF相似度: {tfidf_sim:.4f} (类型 {hazard_type})")
            except Exception as e:
                print(f"⚠️  计算TF-IDF相似度失败: {e}")
                result["tfidf_similarity"] = 0.0

            return result

        except Exception as e:
            print(f"⚠️  结果整合失败，使用直接分类结果: {e}")
            import traceback
            traceback.print_exc()
            
            result = {
                "id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": direct_classification["type"],
                "description": direct_classification["description"],
                "suggestion": self._get_default_suggestion(
                    direct_classification["type"]
                ),
                "confidence": direct_classification["confidence"],
                "similar_cases": [
                    case.get("description", "") for case in similar_cases[:3]
                ],
                "analysis_method": "CLIP Direct Classification (Fallback)",
                "model": model,
                "created_at": datetime.now().isoformat(),
            }
            
            # 即使fallback也计算相似度
            try:
                hazard_type = result["type"]
                generated_desc = result["description"]
                similarity, standard_desc = self.bert_similarity.calculate_similarity(
                    generated_desc, hazard_type
                )
                result["bert_similarity"] = similarity
                result["standard_description"] = standard_desc
            except Exception as e:
                print(f"⚠️  Fallback时计算BERT相似度失败: {e}")
                result["bert_similarity"] = 0.0
                result["standard_description"] = ""
            # 添加 TF-IDF 计算
            try:
                tfidf_sim, _ = self.tfidf_similarity.calculate_similarity(
                    generated_desc, hazard_type
                )
                result["tfidf_similarity"] = tfidf_sim
            except Exception as e:
                print(f"⚠️  Fallback时计算TF-IDF相似度失败: {e}")
                result["tfidf_similarity"] = 0.0
            
            return result

    def _get_default_suggestion(self, hazard_type: str) -> str:
        """获取默认整改建议"""
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
            "15": "立即修复破损电缆，规范电缆敷设，确保用电安全",
        }
        return suggestions.get(
            hazard_type,
            f"针对隐患类型{hazard_type}，请立即整改相关安全隐患，确保符合安全规范要求",
        )

    def _create_error_result(
        self, error_message: str, model: Optional[str] = None
    ) -> Dict:
        """创建错误结果"""
        return {
            "id": f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "unknown",
            "description": f"分析失败: {error_message}",
            "suggestion": "请检查图片质量或重新上传图片",
            "confidence": 0.0,
            "similar_cases": [],
            "analysis_method": "Error",
            "model": model or "unknown",
            "created_at": datetime.now().isoformat(),
            "error": error_message,
            "bert_similarity": 0.0,
            "standard_description": "",
        }

    def batch_analyze(self, image_paths: List[str], top_k: int = 5) -> List[Dict]:
        """批量分析多张图片"""
        results = []
        for i, image_path in enumerate(image_paths, 1):
            print(f"🔄 批量分析进度: {i}/{len(image_paths)} - {image_path}")
            try:
                result = self.analyze_hazard(image_path, top_k=top_k)
                results.append(result)
            except Exception as e:
                error_result = self._create_error_result(str(e))
                error_result["image_path"] = image_path
                results.append(error_result)
        return results

    def get_analysis_statistics(self) -> Dict:
        """获取分析统计信息"""
        try:
            return {
                "total_analyzed": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
                "most_common_type": None,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "error": f"获取统计信息失败: {e}",
                "last_updated": datetime.now().isoformat(),
            }

    def validate_image(self, image_path: str) -> Tuple[bool, str]:
        """验证图片是否适合分析"""
        try:
            if not os.path.exists(image_path):
                return False, "图片文件不存在"

            file_size = os.path.getsize(image_path)
            if file_size > Config.MAX_CONTENT_LENGTH:
                return (
                    False,
                    f"图片文件过大，超过{Config.MAX_CONTENT_LENGTH / 1024 / 1024:.1f}MB限制",
                )

            valid_extensions = [
                ".png",
                ".jpg",
                ".jpeg",
                ".PNG",
                ".JPG",
                ".JPEG",
            ]
            file_ext = os.path.splitext(image_path)[1]
            if file_ext not in valid_extensions:
                return False, f"不支持的图片格式: {file_ext}"

            if not self.image_processor.validate_image(image_path):
                return False, "无效的图片文件"

            return True, "图片验证通过"

        except Exception as e:
            return False, f"图片验证失败: {e}"


