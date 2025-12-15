class HazardModel {
  final String id;
  final String type;
  final String description;
  final String suggestion;
  final double confidence;
  final List<String> similarCases;
  final String model;
  final double? bertSimilarity;
  final double? tfidfSimilarity;
  final String? standardDescription;
  
  // 新增：两个模型的相似度信息
  final Map<String, double>? geminiSimilarity;  // {'bert': 0.85, 'tfidf': 0.78}
  final Map<String, double>? gpt4oSimilarity;    // {'bert': 0.82, 'tfidf': 0.75}

  HazardModel({
    required this.id,
    required this.type,
    required this.description,
    required this.suggestion,
    required this.confidence,
    required this.similarCases,
    required this.model,
    this.bertSimilarity,
    this.tfidfSimilarity,
    this.standardDescription,
    this.geminiSimilarity,
    this.gpt4oSimilarity,
  });

  factory HazardModel.fromJson(Map<String, dynamic> json) {
    return HazardModel(
      id: json['id'] ?? '',
      type: json['type'] ?? '',
      description: json['description'] ?? '',
      suggestion: json['suggestion'] ?? '',
      confidence: (json['confidence'] ?? 0.0).toDouble(),
      similarCases: List<String>.from(json['similar_cases'] ?? []),
      model: json['model'] ?? '',
      bertSimilarity: json['bert_similarity'] != null 
          ? (json['bert_similarity'] as num).toDouble() 
          : null,
      tfidfSimilarity: json['tfidf_similarity'] != null 
          ? (json['tfidf_similarity'] as num).toDouble()
          : null,
      standardDescription: json['standard_description'],
      geminiSimilarity: json['gemini_similarity'] != null
          ? {
              'bert': (json['gemini_similarity']['bert'] as num).toDouble(),
              'tfidf': (json['gemini_similarity']['tfidf'] as num).toDouble(),
            }
          : null,
      gpt4oSimilarity: json['gpt4o_similarity'] != null
          ? {
              'bert': (json['gpt4o_similarity']['bert'] as num).toDouble(),
              'tfidf': (json['gpt4o_similarity']['tfidf'] as num).toDouble(),
            }
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'description': description,
      'suggestion': suggestion,
      'confidence': confidence,
      'similar_cases': similarCases,
      'model': model,
    };
  }
}