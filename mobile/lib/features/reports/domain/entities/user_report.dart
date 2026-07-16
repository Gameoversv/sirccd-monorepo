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
    this.modelVersion,
    this.detectionCount,
    this.modelPrecision,
    this.modelRecall,
    this.modelMap50,
    this.damageRatioRaw,
    this.damageRatioNormalized,
    this.focalScaleFactor,
    this.areaScaleFactor,
    this.weightedDetections,
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
  final String? modelVersion;
  final int? detectionCount;
  final double? modelPrecision;
  final double? modelRecall;
  final double? modelMap50;

  /// Área detectada / área de la imagen, tal como sale del modelo.
  final double? damageRatioRaw;

  /// [damageRatioRaw] corregido por zoom — es el que decide la severidad.
  final double? damageRatioNormalized;

  /// Razón lineal focal_ref/focal_real: 1.0 sin zoom, 0.5 a 2x.
  final double? focalScaleFactor;

  /// Corrección aplicada al ratio de área ([focalScaleFactor] al cuadrado).
  final double? areaScaleFactor;

  /// Suma de confianzas: vía alternativa por la que un reporte llega a ALTA.
  final double? weightedDetections;

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
    modelVersion,
    detectionCount,
    modelPrecision,
    modelRecall,
    modelMap50,
    damageRatioRaw,
    damageRatioNormalized,
    focalScaleFactor,
    areaScaleFactor,
    weightedDetections,
    description,
    rejectionReason,
    createdAt,
    updatedAt,
    reviewedAt,
  ];
}
