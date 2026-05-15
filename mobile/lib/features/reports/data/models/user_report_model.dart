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
    super.description,
    super.rejectionReason,
    required super.createdAt,
    required super.updatedAt,
    super.reviewedAt,
  });

  factory UserReportModel.fromJson(Map<String, dynamic> json) {
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
      imageUrl: json['image_url'] as String,
      annotatedImageUrl: json['annotated_image_url'] as String?,
      description: json['description'] as String?,
      rejectionReason: json['rejection_reason'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      reviewedAt: json['reviewed_at'] != null
          ? DateTime.parse(json['reviewed_at'] as String)
          : null,
    );
  }
}
