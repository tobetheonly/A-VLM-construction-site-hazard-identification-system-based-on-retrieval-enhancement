from flask import Blueprint, request, jsonify
from services.hazard_analyzer import HazardAnalyzer
from services.llm_service import LLMService
from services.cache_service import CacheService
from services.bert_similarity_service import BertSimilarityService
import os
analysis_bp = Blueprint('analysis', __name__)
cache_service = CacheService()
bert_similarity = BertSimilarityService()

@analysis_bp.route('/analyze', methods=['POST'])
def analyze_hazard():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        # 从表单中读取模型选择
        provider = request.form.get('model', 'gemini')
        print(f"📤 收到分析请求: 文件={image_file.filename}, 模型={provider}")

        # 确保上传目录存在
        os.makedirs('uploads', exist_ok=True)
        
        # 保存上传的图片
        image_path = os.path.join('uploads', image_file.filename)
        image_file.save(image_path)
        print(f"💾 图片已保存到: {image_path}")

        # 计算图片哈希值
        image_hash = cache_service.calculate_image_hash(image_path)
        
        # 检查两个模型的缓存
        gemini_result = cache_service.get_cached_result(image_hash, 'gemini')
        gpt4o_result = cache_service.get_cached_result(image_hash, 'gpt4o')
        
        # 如果当前请求的模型有缓存，直接返回
        cached_result = cache_service.get_cached_result(image_hash, provider)
        if cached_result:
            print(f"✅ 使用缓存结果，跳过 LLM 调用")
            # 清理临时文件
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # 返回结果，包含两个模型的信息
            result_data = cached_result['result']
            result_data['gemini_similarity'] = {
                'bert': gemini_result['result'].get('bert_similarity', 0.0) if gemini_result else 0.0,
                'tfidf': gemini_result['result'].get('tfidf_similarity', 0.0) if gemini_result else 0.0,
            }
            result_data['gpt4o_similarity'] = {
                'bert': gpt4o_result['result'].get('bert_similarity', 0.0) if gpt4o_result else 0.0,
                'tfidf': gpt4o_result['result'].get('tfidf_similarity', 0.0) if gpt4o_result else 0.0,
            }
            
            return jsonify(result_data)

        # 缓存未命中，进行实际分析
        print(f"🔄 缓存未命中，开始分析 (hash: {image_hash[:8]}..., model: {provider})")
        llm_service = LLMService()
        analyzer = HazardAnalyzer(llm_service)
        result = analyzer.analyze_hazard(image_path, provider=provider)

        # 保存到缓存（检查返回值）
        print(f"💾 准备保存分析结果到缓存...")
        cache_saved = cache_service.save_result(image_hash, result, provider)
        
        if cache_saved:
            print(f"✅ 分析结果已成功保存到 MongoDB")
        else:
            print(f"❌ 警告：分析结果保存失败！但继续返回结果")

        # 保存后再获取两个模型的缓存结果
        gemini_result = cache_service.get_cached_result(image_hash, 'gemini')
        gpt4o_result = cache_service.get_cached_result(image_hash, 'gpt4o')
        
        # 添加两个模型的相似度信息
        result['gemini_similarity'] = {
            'bert': gemini_result['result'].get('bert_similarity', 0.0) if gemini_result else 0.0,
            'tfidf': gemini_result['result'].get('tfidf_similarity', 0.0) if gemini_result else 0.0,
        }
        result['gpt4o_similarity'] = {
            'bert': gpt4o_result['result'].get('bert_similarity', 0.0) if gpt4o_result else 0.0,
            'tfidf': gpt4o_result['result'].get('tfidf_similarity', 0.0) if gpt4o_result else 0.0,
        }
        
        # 清理临时文件
        if os.path.exists(image_path):
            os.remove(image_path)

        return jsonify(result)

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@analysis_bp.route('/similarity/stats', methods=['GET'])
def get_similarity_stats():
    """获取相似度统计信息"""
    try:
        stats = bert_similarity.get_average_similarity()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'获取相似度统计失败: {str(e)}'}), 500

@analysis_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """获取缓存统计信息"""
    try:
        stats = cache_service.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500


@analysis_bp.route('/similarity/averages', methods=['GET'])
def get_average_similarities():
    """获取所有模型的平均相似度统计（BERT 和 TF-IDF）"""
    try:
        from pymongo import MongoClient
        from config import Config
        
        client = MongoClient(Config.MONGODB_URI)
        db = client[Config.DATABASE_NAME]
        cache_collection = db.analysis_cache
        
        stats = {
            'gemini': {
                'bert_avg': 0.0,
                'tfidf_avg': 0.0,
                'count': 0
            },
            'gpt4o': {
                'bert_avg': 0.0,
                'tfidf_avg': 0.0,
                'count': 0
            }
        }
        
        # 获取所有缓存记录
        all_caches = list(cache_collection.find({}))
        
        for cache in all_caches:
            model = cache.get('model', '')
            result = cache.get('result', {})
            
            if model in ['gemini', 'gpt4o']:
                bert_sim = result.get('bert_similarity', 0.0)
                tfidf_sim = result.get('tfidf_similarity', 0.0)
                
                if bert_sim > 0 or tfidf_sim > 0:
                    stats[model]['count'] += 1
                    stats[model]['bert_avg'] += bert_sim
                    stats[model]['tfidf_avg'] += tfidf_sim
        
        # 计算平均值
        for model in ['gemini', 'gpt4o']:
            if stats[model]['count'] > 0:
                stats[model]['bert_avg'] /= stats[model]['count']
                stats[model]['tfidf_avg'] /= stats[model]['count']
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'获取平均相似度失败: {str(e)}'}), 500