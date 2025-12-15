import 'dart:io';
import 'package:flutter/material.dart';
import 'dart:typed_data';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../models/hazard_model.dart';
import '../widgets/result_display.dart';
import '../widgets/image_upload_widget.dart';
import '../widgets/similarity_display.dart';

// 隐患识别系统主界面
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  File? _selectedImage;
  Uint8List? _selectedImageBytes;
  HazardModel? _analysisResult;
  bool _isLoading = false;
  // 当前选择的模型：'gemini' 或 'gpt4o'
  String _selectedModel = 'gemini';
  
  // 平均相似度统计
  Map<String, dynamic>? _averageStats;

  @override
  void initState() {
    super.initState();
    _loadAverageStats();
  }

  // 加载平均相似度统计
  Future<void> _loadAverageStats() async {
    try {
      final stats = await ApiService.getAverageSimilarities();
      setState(() {
        _averageStats = stats;
      });
    } catch (e) {
      print('获取平均相似度失败: $e');
      // 设置默认值
      setState(() {
        _averageStats = {
          'gemini': {'bert_avg': 0.0, 'tfidf_avg': 0.0, 'count': 0},
          'gpt4o': {'bert_avg': 0.0, 'tfidf_avg': 0.0, 'count': 0},
        };
      });
    }
  }

  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
    );

    if (image != null) {
      final bytes = await image.readAsBytes();

      setState(() {
        _selectedImage = File(image.path);
        _selectedImageBytes = bytes;
        _analysisResult = null;
      });
      await _analyzeImage();
    }
  }

  Future<void> _analyzeImage() async {
    if (_selectedImage == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.uploadImage(
        _selectedImage!,
        _selectedImageBytes,
        _selectedModel,
      );
      setState(() {
        _analysisResult = result;
        _isLoading = false;
      });
      // 分析完成后刷新平均统计
      _loadAverageStats();
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('分析失败: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('隐患识别系统'),
        backgroundColor: Colors.blue[600],
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // 第一行：模型选择（左侧）
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 左侧：模型选择
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '选择模型：',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        ChoiceChip(
                          label: const Text('Gemini'),
                          selected: _selectedModel == 'gemini',
                          onSelected: (selected) {
                            if (selected) {
                              setState(() {
                                _selectedModel = 'gemini';
                              });
                              if (_selectedImage != null) {
                                _analyzeImage();
                              }
                            }
                          },
                        ),
                        const SizedBox(width: 8),
                        ChoiceChip(
                          label: const Text('GPT-4o'),
                          selected: _selectedModel == 'gpt4o',
                          onSelected: (selected) {
                            if (selected) {
                              setState(() {
                                _selectedModel = 'gpt4o';
                              });
                              if (_selectedImage != null) {
                                _analyzeImage();
                              }
                            }
                          },
                        ),
                      ],
                    ),
                  ],
                ),

                const SizedBox(width: 4),//向左移动，越小越近

                // 中间：图片上传区域
                Expanded(
                  flex: 3,//修改宽度
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 100),  // 向下移动 50 像素
                      Transform.translate(
                        offset: const Offset(-100, 0),  // 向左移动 50 像素（负值向左，正值向右）
                        child: ImageUploadWidget(
                          selectedImage: _selectedImage,
                          selectedImageBytes: _selectedImageBytes,
                          onImageSelected: (File image, Uint8List? bytes) {
                            setState(() {
                              _selectedImage = image;
                              _selectedImageBytes = bytes;
                              _analysisResult = null;
                            });
                            if (image.path.isNotEmpty) {
                              _analyzeImage();
                            }
                          },
                          onPickImage: _pickImage,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // 加载状态
                      if (_isLoading)
                        const Row(
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            SizedBox(width: 8),
                            Text(
                              '正在分析图片，请稍候...',
                              style: TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),

                const SizedBox(width: 16),

                // 右侧：相似度展示
                Expanded(
                  flex: 3,
                  child: SimilarityDisplay(
                    result: _analysisResult,
                    averageStats: _averageStats,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // 第二行：详细结果展示（单独一行，占满宽度）
            Expanded(
              child: _analysisResult != null && !_isLoading
                  ? ResultDisplay(
                      result: _analysisResult!,
                      averageStats: _averageStats,
                    )
                  : Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.description_outlined,
                              size: 64,
                              color: Colors.grey[400],
                            ),
                            const SizedBox(height: 16),
                            Text(
                              '详细结果将显示在这里',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 16,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}