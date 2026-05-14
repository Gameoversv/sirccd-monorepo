import 'dart:async';

import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';
import 'package:sirccd_mobile/core/services/connectivity_service.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:sirccd_mobile/features/reports/data/datasources/report_local_datasource.dart';
import 'package:sirccd_mobile/features/reports/data/datasources/report_remote_datasource.dart';
import 'package:sirccd_mobile/features/reports/data/models/pending_report_model.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';
import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';

final class ReportRepositoryImpl implements ReportRepository {
  ReportRepositoryImpl(
    this._local,
    this._remote,
    this._auth,
    this._connectivity,
  ) : _refreshController = StreamController<List<PendingReport>>.broadcast();

  final ReportLocalDataSource _local;
  final ReportRemoteDataSource _remote;
  final AuthLocalDataSource _auth;
  final ConnectivityService _connectivity;
  final StreamController<List<PendingReport>> _refreshController;

  static const _uuid = Uuid();

  @override
  Future<PendingReport> createPendingReport({
    required String imagePath,
    required double latitude,
    required double longitude,
    String? description,
    String? address,
    String? city,
    String? province,
  }) async {
    final report = PendingReportModel(
      localId: _uuid.v4(),
      imagePath: imagePath,
      latitude: latitude,
      longitude: longitude,
      description: description?.trim().isEmpty ?? true ? null : description?.trim(),
      address: address?.trim().isEmpty ?? true ? null : address?.trim(),
      city: city?.trim().isEmpty ?? true ? null : city?.trim(),
      province: province?.trim().isEmpty ?? true ? null : province?.trim(),
      syncStatus: SyncStatus.pending,
      createdAt: DateTime.now(),
    );
    await _local.insert(report);
    await _notifyRefresh();

    final isOnline = await _connectivity.isConnected();
    if (isOnline) unawaited(_syncOne(report));

    return report;
  }

  @override
  Stream<List<PendingReport>> watchAllReports() async* {
    yield await _local.getAll();
    yield* _refreshController.stream;
  }

  @override
  Future<void> syncPendingReports() async {
    final pending = await _local.getByStatus(SyncStatus.pending);
    final failed = await _local.getByStatus(SyncStatus.failed);
    for (final report in [...pending, ...failed]) {
      await _syncOne(report);
    }
  }

  Future<void> _syncOne(PendingReportModel report) async {
    final token = await _auth.getToken();
    if (token == null) return;

    try {
      await _local.updateStatus(report.localId, SyncStatus.syncing);
      await _notifyRefresh();

      final serverId = await _remote.submitReport(report, token);

      await _local.updateStatus(
        report.localId,
        SyncStatus.synced,
        serverId: serverId,
      );
    } on DioException catch (e) {
      final msg = e.response?.data?.toString() ?? e.message ?? 'Error de red';
      await _local.updateStatus(
        report.localId,
        SyncStatus.failed,
        error: msg,
      );
    } catch (e) {
      await _local.updateStatus(
        report.localId,
        SyncStatus.failed,
        error: '$e',
      );
    } finally {
      await _notifyRefresh();
    }
  }

  Future<void> _notifyRefresh() async {
    if (_refreshController.isClosed) return;
    final reports = await _local.getAll();
    _refreshController.add(reports);
  }
}
