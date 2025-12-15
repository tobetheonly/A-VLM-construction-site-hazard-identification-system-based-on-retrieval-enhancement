from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from config import Config
import os
from datetime import datetime

history_bp = Blueprint('history', __name__)

def get_db_connection():
    """获取数据库连接"""
    try:
        client = MongoClient(Config.MONGODB_URI)
        db = client[Config.DATABASE_NAME]
        return db
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

@history_bp.route('/history', methods=['GET'])
def get_history_cases():
    """获取历史案例列表"""
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        hazard_type = request.args.get('type', None)
        
        # 构建查询条件
        query = {}
        if hazard_type:
            query['type'] = hazard_type
        
        # 计算跳过的文档数量
        skip = (page - 1) * limit
        
        # 查询历史案例
        cases = list(db.cases.find(
            query,
            {
                '_id': 1,
                'filename': 1,
                'type': 1,
                'image_id': 1,
                'description': 1,
                'category_description': 1,
                'suggestion': 1,
                'created_at': 1,
                'file_size': 1,
                'file_type': 1
            }
        ).skip(skip).limit(limit).sort('created_at', -1))
        
        # 获取总数
        total = db.cases.count_documents(query)
        
        # 转换ObjectId为字符串
        for case in cases:
            case['_id'] = str(case['_id'])
            if 'created_at' in case:
                case['created_at'] = case['created_at'].isoformat()
        
        return jsonify({
            'cases': cases,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        return jsonify({'error': f'获取历史案例失败: {str(e)}'}), 500

@history_bp.route('/history/<string:case_id>', methods=['GET'])
def get_history_case_detail(case_id):
    """获取特定历史案例详情"""
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 查询特定案例
        case = db.cases.find_one({'_id': case_id})
        
        if not case:
            return jsonify({'error': '案例不存在'}), 404
        
        # 移除特征向量（太大）
        case.pop('features', None)
        case['_id'] = str(case['_id'])
        
        if 'created_at' in case:
            case['created_at'] = case['created_at'].isoformat()
        if 'updated_at' in case:
            case['updated_at'] = case['updated_at'].isoformat()
        
        return jsonify(case)
        
    except Exception as e:
        return jsonify({'error': f'获取案例详情失败: {str(e)}'}), 500

@history_bp.route('/history/statistics', methods=['GET'])
def get_statistics():
    """获取历史案例统计信息"""
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 总案例数
        total_cases = db.cases.count_documents({})
        
        # 按类型统计
        type_pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        type_stats = list(db.cases.aggregate(type_pipeline))
        
        # 按文件类型统计
        file_type_pipeline = [
            {"$group": {"_id": "$file_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        file_type_stats = list(db.cases.aggregate(file_type_pipeline))
        
        # 最近添加的案例
        recent_cases = list(db.cases.find(
            {},
            {
                '_id': 1,
                'filename': 1,
                'type': 1,
                'created_at': 1
            }
        ).sort('created_at', -1).limit(5))
        
        # 转换ObjectId和日期
        for case in recent_cases:
            case['_id'] = str(case['_id'])
            if 'created_at' in case:
                case['created_at'] = case['created_at'].isoformat()
        
        return jsonify({
            'total_cases': total_cases,
            'type_statistics': type_stats,
            'file_type_statistics': file_type_stats,
            'recent_cases': recent_cases
        })
        
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@history_bp.route('/history/search', methods=['GET'])
def search_history_cases():
    """搜索历史案例"""
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 获取搜索参数
        query_text = request.args.get('q', '')
        hazard_type = request.args.get('type', None)
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 构建查询条件
        query = {}
        
        if hazard_type:
            query['type'] = hazard_type
        
        if query_text:
            # 文本搜索
            query['$text'] = {'$search': query_text}
        
        # 计算跳过的文档数量
        skip = (page - 1) * limit
        
        # 执行搜索
        if query_text:
            # 文本搜索，按相关性排序
            cases = list(db.cases.find(
                query,
                {
                    '_id': 1,
                    'filename': 1,
                    'type': 1,
                    'image_id': 1,
                    'description': 1,
                    'category_description': 1,
                    'suggestion': 1,
                    'created_at': 1,
                    'score': {'$meta': 'textScore'}
                }
            ).sort([('score', {'$meta': 'textScore'})]).skip(skip).limit(limit))
        else:
            # 普通查询
            cases = list(db.cases.find(
                query,
                {
                    '_id': 1,
                    'filename': 1,
                    'type': 1,
                    'image_id': 1,
                    'description': 1,
                    'category_description': 1,
                    'suggestion': 1,
                    'created_at': 1
                }
            ).skip(skip).limit(limit).sort('created_at', -1))
        
        # 获取总数
        total = db.cases.count_documents(query)
        
        # 转换ObjectId为字符串
        for case in cases:
            case['_id'] = str(case['_id'])
            if 'created_at' in case:
                case['created_at'] = case['created_at'].isoformat()
        
        return jsonify({
            'cases': cases,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'query': query_text
        })
        
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@history_bp.route('/history/delete/<string:case_id>', methods=['DELETE'])
def delete_history_case(case_id):
    """删除历史案例"""
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 删除案例
        result = db.cases.delete_one({'_id': case_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': '案例不存在'}), 404
        
        return jsonify({'message': '案例删除成功'})
        
    except Exception as e:
        return jsonify({'error': f'删除案例失败: {str(e)}'}), 500

@history_bp.route('/history/export', methods=['GET'])
def export_history_cases():
    """导出历史案例数据"""
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 获取所有案例（不包含特征向量）
        cases = list(db.cases.find(
            {},
            {
                'filename': 1,
                'type': 1,
                'image_id': 1,
                'description': 1,
                'category_description': 1,
                'suggestion': 1,
                'created_at': 1,
                'updated_at': 1,
                'file_size': 1,
                'file_type': 1
            }
        ))
        
        # 转换日期格式
        for case in cases:
            case['_id'] = str(case['_id'])
            if 'created_at' in case:
                case['created_at'] = case['created_at'].isoformat()
            if 'updated_at' in case:
                case['updated_at'] = case['updated_at'].isoformat()
        
        return jsonify({
            'cases': cases,
            'total': len(cases),
            'export_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'导出数据失败: {str(e)}'}), 500

# 错误处理
@history_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API端点不存在'}), 404

@history_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500