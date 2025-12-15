//import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'dart:typed_data';
import '../models/hazard_model.dart';
//有报错
class ApiService {
  static const String baseUrl = 'http://localhost:5000/api';
  static final Dio _dio = Dio();


  // 获取平均相似度统计
  static Future<Map<String, dynamic>> getAverageSimilarities() async {
    try {
      Response response = await _dio.get('$baseUrl/similarity/averages');
      if (response.statusCode == 200) {
        return Map<String, dynamic>.from(response.data);
      }
      throw Exception('获取平均相似度失败');
    } catch (e) {
      throw Exception('获取平均相似度失败: $e');
    }
  }
   
  // 上传图片并获取隐患识别结果
  static Future<HazardModel> uploadImage(
    File imageFile,
    Uint8List? imageBytes,
    String model, // 新增：模型选择（'gemini' 或 'gpt4o'）
  ) async {
    try {
      String fileName = imageFile.path.split('/').last;

      FormData formData;

      if (imageBytes != null) {
        // 使用字节数据上传
        formData = FormData.fromMap({
          'image': MultipartFile.fromBytes(
            imageBytes,
            filename: fileName,
            contentType: DioMediaType.parse('image/jpeg'),
          ),
          'model': model,
        });
      } else {
        // 使用文件上传
        formData = FormData.fromMap({
          'image': await MultipartFile.fromFile(
            imageFile.path,
            filename: fileName,
          ),
          'model': model,
        });
      }

      Response response = await _dio.post(
        '$baseUrl/analyze',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
          receiveTimeout: const Duration(minutes: 5),
          sendTimeout: const Duration(minutes: 2),
        ),
      );

      if (response.statusCode == 200) {
        return HazardModel.fromJson(response.data);
      } else {
        throw Exception('分析失败: ${response.statusMessage}');
      }
    } catch (e) {
      throw Exception('网络请求失败: $e');
    }
  }

  // 获取历史案例
  static Future<List<Map<String, dynamic>>> getHistoryCases() async {
    try {
      Response response = await _dio.get('$baseUrl/history');
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(response.data);
      }
      throw Exception('获取历史案例失败');
    } catch (e) {
      throw Exception('获取历史案例失败: $e');
    }
  }

  // 检查服务器连接状态
  static Future<bool> checkConnection() async {
    try {
      Response response = await _dio.get(
        '$baseUrl/health',
        options: Options(receiveTimeout: const Duration(seconds: 5)),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}