import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';

final class PendingReportModel extends PendingReport {
  const PendingReportModel({
    required super.localId,
    required super.imagePath,
    required super.latitude,
    required super.longitude,
    super.description,
    super.address,
    super.city,
    super.province,
    super.focalScaleFactor,
    required super.syncStatus,
    super.serverId,
    super.syncError,
    required super.createdAt,
  });

  factory PendingReportModel.fromMap(Map<String, dynamic> map) =>
      PendingReportModel(
        localId: map['local_id'] as String,
        imagePath: map['image_path'] as String,
        latitude: (map['latitude'] as num).toDouble(),
        longitude: (map['longitude'] as num).toDouble(),
        description: map['description'] as String?,
        address: map['address'] as String?,
        city: map['city'] as String?,
        province: map['province'] as String?,
        focalScaleFactor: (map['focal_scale_factor'] as num?)?.toDouble(),
        syncStatus: SyncStatus.values.firstWhere(
          (s) => s.name == map['sync_status'],
          orElse: () => SyncStatus.pending,
        ),
        serverId: map['server_id'] as int?,
        syncError: map['sync_error'] as String?,
        createdAt: DateTime.parse(map['created_at'] as String),
      );

  Map<String, dynamic> toMap() => {
    'local_id': localId,
    'image_path': imagePath,
    'latitude': latitude,
    'longitude': longitude,
    'description': description,
    'address': address,
    'city': city,
    'province': province,
    'focal_scale_factor': focalScaleFactor,
    'sync_status': syncStatus.name,
    'server_id': serverId,
    'sync_error': syncError,
    'created_at': createdAt.toIso8601String(),
  };
}
