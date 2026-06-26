import 'package:sirccd_mobile/core/services/database_service.dart';
import 'package:sirccd_mobile/features/reports/data/models/pending_report_model.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';

abstract interface class ReportLocalDataSource {
  Future<void> insert(PendingReportModel report);
  Future<List<PendingReportModel>> getAll();
  Future<List<PendingReportModel>> getByStatus(SyncStatus status);
  Future<void> updateStatus(
    String localId,
    SyncStatus status, {
    int? serverId,
    String? error,
  });
  Future<void> deleteAll();
}

final class ReportLocalDataSourceImpl implements ReportLocalDataSource {
  const ReportLocalDataSourceImpl(this._db);

  final DatabaseService _db;

  static const _table = 'pending_reports';

  @override
  Future<void> insert(PendingReportModel report) async {
    final db = await _db.database;
    await db.insert(_table, report.toMap());
  }

  @override
  Future<List<PendingReportModel>> getAll() async {
    final db = await _db.database;
    final rows = await db.query(
      _table,
      orderBy: 'created_at DESC',
    );
    return rows.map(PendingReportModel.fromMap).toList();
  }

  @override
  Future<List<PendingReportModel>> getByStatus(SyncStatus status) async {
    final db = await _db.database;
    final rows = await db.query(
      _table,
      where: 'sync_status = ?',
      whereArgs: [status.name],
      orderBy: 'created_at ASC',
    );
    return rows.map(PendingReportModel.fromMap).toList();
  }

  @override
  Future<void> updateStatus(
    String localId,
    SyncStatus status, {
    int? serverId,
    String? error,
  }) async {
    final db = await _db.database;
    await db.update(
      _table,
      {
        'sync_status': status.name,
        if (serverId != null) 'server_id': serverId,
        if (error != null) 'sync_error': error,
        if (status == SyncStatus.syncing) 'sync_error': null,
      },
      where: 'local_id = ?',
      whereArgs: [localId],
    );
  }

  @override
  Future<void> deleteAll() async {
    final db = await _db.database;
    await db.delete(_table);
  }
}
