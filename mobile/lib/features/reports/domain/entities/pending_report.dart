import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';

class PendingReport extends Equatable {
  const PendingReport({
    required this.localId,
    required this.imagePath,
    required this.latitude,
    required this.longitude,
    this.description,
    this.address,
    this.city,
    this.province,
    required this.syncStatus,
    this.serverId,
    this.syncError,
    required this.createdAt,
  });

  final String localId;
  final String imagePath;
  final double latitude;
  final double longitude;
  final String? description;
  final String? address;
  final String? city;
  final String? province;
  final SyncStatus syncStatus;
  final int? serverId;
  final String? syncError;
  final DateTime createdAt;

  PendingReport copyWith({
    String? localId,
    String? imagePath,
    double? latitude,
    double? longitude,
    String? description,
    String? address,
    String? city,
    String? province,
    SyncStatus? syncStatus,
    int? serverId,
    String? syncError,
    DateTime? createdAt,
  }) =>
      PendingReport(
        localId: localId ?? this.localId,
        imagePath: imagePath ?? this.imagePath,
        latitude: latitude ?? this.latitude,
        longitude: longitude ?? this.longitude,
        description: description ?? this.description,
        address: address ?? this.address,
        city: city ?? this.city,
        province: province ?? this.province,
        syncStatus: syncStatus ?? this.syncStatus,
        serverId: serverId ?? this.serverId,
        syncError: syncError ?? this.syncError,
        createdAt: createdAt ?? this.createdAt,
      );

  @override
  List<Object?> get props => [
        localId,
        imagePath,
        latitude,
        longitude,
        description,
        address,
        city,
        province,
        syncStatus,
        serverId,
        syncError,
        createdAt,
      ];
}
