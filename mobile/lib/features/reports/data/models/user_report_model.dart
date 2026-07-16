import 'dart:convert';

import 'package:sirccd_mobile/core/network/backend_url.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/damage_type.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/severity_level.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';

class UserReportModel extends UserReport {
  const UserReportModel({
    required super.id,
    required super.latitude,
    required super.longitude,
    super.address,
    super.city,
    super.province,
    required super.status,
    super.damageType,
    super.severity,
    super.confidence,
    required super.imageUrl,
    super.annotatedImageUrl,
    super.modelVersion,
    super.detectionCount,
    super.modelPrecision,
    super.modelRecall,
    super.modelMap50,
    super.description,
    super.rejectionReason,
    required super.createdAt,
    required super.updatedAt,
    super.reviewedAt,
  });

  factory UserReportModel.fromJson(Map<String, dynamic> json) {
    final detections = _decodeDetections(json['detections_json']);

    return UserReportModel(
      id: (json['id'] as num).toInt(),
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      address: json['address'] as String?,
      city: json['city'] as String?,
      province: json['province'] as String?,
      status: ReportStatus.fromString(json['status'] as String? ?? ''),
      damageType: DamageType.fromString(json['damage_type'] as String?),
      severity: SeverityLevel.fromString(json['severity'] as String?),
      confidence: json['confidence'] != null
          ? (json['confidence'] as num).toDouble()
          : null,
      imageUrl: BackendUrl.normalizeAssetUrl(json['image_url'] as String),
      annotatedImageUrl: BackendUrl.normalizeNullableAssetUrl(
        _stringValue(json['annotated_image_url']) ??
            _stringValue(detections?['annotated_image_url']),
      ),
      modelVersion:
          _stringValue(json['model_version']) ??
          _stringValue(detections?['model_version']),
      detectionCount:
          _intValue(json['num_detections']) ??
          _intValue(detections?['num_detections']) ??
          _listLength(detections?['bounding_boxes']),
      modelPrecision:
          _doubleValue(json['model_precision']) ??
          _doubleValue(detections?['model_precision']),
      modelRecall:
          _doubleValue(json['model_recall']) ??
          _doubleValue(detections?['model_recall']),
      modelMap50:
          _doubleValue(json['model_map50']) ??
          _doubleValue(detections?['model_map50']),
      description: json['description'] as String?,
      rejectionReason: json['rejection_reason'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      reviewedAt: json['reviewed_at'] != null
          ? DateTime.parse(json['reviewed_at'] as String)
          : null,
    );
  }

  static Map<String, dynamic>? _decodeDetections(Object? value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    if (value is! String || value.trim().isEmpty) return null;

    try {
      final decoded = jsonDecode(value);
      if (decoded is Map<String, dynamic>) return decoded;
      if (decoded is Map) return Map<String, dynamic>.from(decoded);
    } catch (_) {
      return null;
    }
    return null;
  }

  static String? _stringValue(Object? value) {
    if (value is String && value.isNotEmpty) return value;
    return null;
  }

  static double? _doubleValue(Object? value) {
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }

  static int? _intValue(Object? value) {
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value);
    return null;
  }

  static int? _listLength(Object? value) {
    if (value is List) return value.length;
    return null;
  }
}
