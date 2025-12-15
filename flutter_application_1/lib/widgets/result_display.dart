import 'package:flutter/material.dart';
import '../models/hazard_model.dart';

class ResultDisplay extends StatelessWidget {
  final HazardModel result;
  final Map<String, dynamic>? averageStats;  // 新增参数

  const ResultDisplay({
    super.key,
    required this.result,
    this.averageStats,  // 新增
  });
  
// 添加辅助方法
  Color _getSimilarityColor(double similarity) {
    if (similarity >= 0.8) return Colors.green[600]!;
    if (similarity >= 0.6) return Colors.orange[600]!;
    return Colors.red[600]!;
  }
  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 6,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        height: double.infinity,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 使用模型信息
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '使用模型：${result.model.isEmpty ? '未知' : result.model.toUpperCase()}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[700],
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 标题
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.orange[50],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      Icons.warning_amber_rounded,
                      color: Colors.orange[600],
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      '隐患识别结果',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.orange[700],
                          ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // 隐患类型和隐患描述（合并到第一个框）
              _buildInfoCard(
                icon: Icons.category,
                title: '隐患类型与描述',
                content: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.red[100],
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '类型 ${result.type}',
                        style: TextStyle(
                          color: Colors.red[800],
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      result.description,
                      style: TextStyle(
                        color: Colors.red[900],
                        fontSize: 14,
                        height: 1.6,
                      ),
                    ),
                  ],
                ),
                color: Colors.red[50]!,
                textColor: Colors.red[700]!,
                iconColor: Colors.red[600]!,
              ),

              const SizedBox(height: 16),

              // 置信度
              _buildInfoCard(
                icon: Icons.analytics,
                title: 'LLM识别置信度',
                content: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.blue[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.trending_up, color: Colors.blue[700], size: 20),
                      const SizedBox(width: 8),
                      Text(
                        '${(result.confidence * 100).toStringAsFixed(1)}%',
                        style: TextStyle(
                          color: Colors.blue[800],
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                color: Colors.blue[50]!,
                textColor: Colors.blue[700]!,
                iconColor: Colors.blue[600]!,
              ),
              
            
              const SizedBox(height: 16),

// BERT语义相似度
              if (result.bertSimilarity != null || result.tfidfSimilarity != null)
                _buildInfoCard(
                  icon: Icons.auto_awesome,
                  title: '文本相似度指标',
                  color: Colors.purple[50]!,  // 添加这一行
                  textColor: Colors.purple[700]!,  // 添加这一行
                  iconColor: Colors.purple[600]!,  // 添加这一行
                  content: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // BERT 语义相似度
                      if (result.bertSimilarity != null) ...[
                        Row(
                          children: [
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                decoration: BoxDecoration(
                                  color: _getSimilarityColor(result.bertSimilarity!),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      Icons.psychology,
                                      color: Colors.white,
                                      size: 18,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      'BERT: ${(result.bertSimilarity! * 100).toStringAsFixed(2)}%',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                      ],
                      // TF-IDF 文本相似度
                      if (result.tfidfSimilarity != null) ...[
                        Row(
                          children: [
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                decoration: BoxDecoration(
                                  color: _getSimilarityColor(result.tfidfSimilarity!),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      Icons.text_fields,
                                      color: Colors.white,
                                      size: 18,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      'TF-IDF: ${(result.tfidfSimilarity! * 100).toStringAsFixed(2)}%',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                      // 标准描述
                      if (result.standardDescription != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '标准描述：',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                result.standardDescription!,
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey[800],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),

              const SizedBox(height: 16),

              // 整改建议
              _buildInfoCard(
                icon: Icons.build,
                title: '整改建议',
                content: Text(
                  result.suggestion,
                  style: TextStyle(
                    color: Colors.green[900],
                    fontSize: 14,
                    height: 1.6,
                  ),
                ),
                color: Colors.green[50]!,
                textColor: Colors.green[700]!,
                iconColor: Colors.green[600]!,
              ),

              if (result.similarCases.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildSimilarCases(),
              ],

              const SizedBox(height: 20), // 底部留白
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard({
    required IconData icon,
    required String title,
    required Widget content,
    required Color color,
    required Color textColor,
    required Color iconColor,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: textColor.withOpacity(0.2),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: textColor.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: iconColor, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: textColor,
                    fontSize: 16,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          content,
        ],
      ),
    );
  }

  Widget _buildSimilarCases() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.purple[50]!,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.purple.withOpacity(0.2),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.purple.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.purple[200],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.find_in_page,
                  color: Colors.purple[700]!,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '相似案例',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.purple[700]!,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...result.similarCases.take(3).map(
                (caseItem) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        margin: const EdgeInsets.only(top: 6),
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: Colors.purple[400]!,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            caseItem,
                            style: TextStyle(
                              color: Colors.purple[800],
                              fontSize: 13,
                              height: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
        ],
      ),
    );
  }
}