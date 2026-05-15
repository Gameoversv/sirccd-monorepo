import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/damage_type.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/severity_level.dart';

class UserReport extends Equatable {
  const UserReport({
    required this.id,
    required this.latitude,
    required this.longitude,
    this.address,
    this.city,
    this.province,
    required this.status,
    this.damageType,
    this.severity,
    this.confidence,
    required this.imageUrl,
    this.annotatedImageUrl,
    this.description,
    this.rejectionReason,
    required this.createdAt,
    required this.updatedAt,
    this.reviewedAt,
  });

  final int id;
  final double latitude;
  final double longitude;
  final String? address;
  final String? city;
  final String? province;
  final ReportStatus status;
  final DamageType? damageType;
  final SeverityLevel? severity;
  final double? confidence;
  final String imageUrl;
  final String? annotatedImageUrl;
  final String? description;
  final String? rejectionReason;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? reviewedAt;

  @override
  List<Object?> get props => [
        id,
        latitude,
        longitude,
        address,
        city,
        province,
        status,
        damageType,
        severity,
        confidence,
        imageUrl,
        annotatedImageUrl,
        description,
        rejectionReason,
        createdAt,
        updatedAt,
        reviewedAt,
      ];
}
