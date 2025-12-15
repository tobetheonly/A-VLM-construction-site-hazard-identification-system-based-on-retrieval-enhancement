import 'package:flutter/material.dart';
import '../models/hazard_model.dart';

class SimilarityDisplay extends StatelessWidget {
  final HazardModel? result;
  final Map<String, dynamic>? averageStats;

  const SimilarityDisplay({
    super.key,
    this.result,
    this.averageStats,
  });

  Color _getSimilarityColor(double similarity) {
    if (similarity >= 0.8) return Colors.green[600]!;
    if (similarity >= 0.6) return Colors.orange[600]!;
    return Colors.red[600]!;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 标题
              Row(
                children: [
                  Icon(Icons.auto_awesome, color: Colors.purple[600], size: 24),
                  const SizedBox(width: 8),
                  Text(
                    '文本相似度指标',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.purple[700],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Gemini 模型相似度
              _buildModelSection(
                'Gemini',
                result?.geminiSimilarity,
                averageStats?['gemini'],
              ),

              const SizedBox(height: 16),

              // GPT-4o 模型相似度
              _buildModelSection(
                'GPT-4o',
                result?.gpt4oSimilarity,
                averageStats?['gpt4o'],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModelSection(
    String modelName,
    Map<String, double>? currentSimilarity,
    Map<String, dynamic>? averageStats,
  ) {
    final bertCurrent = currentSimilarity?['bert'] ?? 0.0;
    final tfidfCurrent = currentSimilarity?['tfidf'] ?? 0.0;
    final bertAvg = (averageStats?['bert_avg'] ?? 0.0).toDouble();
    final tfidfAvg = (averageStats?['tfidf_avg'] ?? 0.0).toDouble();
    final count = averageStats?['count'] ?? 0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 模型名称
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: modelName == 'Gemini' 
                      ? Colors.blue[100] 
                      : Colors.green[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  modelName,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: modelName == 'Gemini' 
                        ? Colors.blue[800] 
                        : Colors.green[800],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // 当前示例相似度
          Text(
            '当前示例',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _buildSimilarityBadge(
                  'BERT',
                  bertCurrent,
                  Icons.psychology,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildSimilarityBadge(
                  'TF-IDF',
                  tfidfCurrent,
                  Icons.text_fields,
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // 平均相似度
          Text(
            '数据库平均值',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.psychology, color: Colors.grey[700], size: 16),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'BERT: ${(bertAvg * 100).toStringAsFixed(2)}%',
                          style: TextStyle(
                            color: Colors.grey[800],
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.text_fields, color: Colors.grey[700], size: 16),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'TF-IDF: ${(tfidfAvg * 100).toStringAsFixed(2)}%',
                          style: TextStyle(
                            color: Colors.grey[800],
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          if (count > 0) ...[
            const SizedBox(height: 6),
            Text(
              '基于 $count 条记录',
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey[500],
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSimilarityBadge(String label, double value, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: _getSimilarityColor(value),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white, size: 18),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              '$label: ${(value * 100).toStringAsFixed(2)}%',
              style: TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}