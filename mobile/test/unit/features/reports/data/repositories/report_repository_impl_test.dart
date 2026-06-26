import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/reports/data/datasources/report_local_datasource.dart';
import 'package:sirccd_mobile/features/reports/data/models/pending_report_model.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';

// ── Fakes ──────────────────────────────────────────────────────────────────

class _FakeLocalDataSource implements ReportLocalDataSource {
  final List<PendingReportModel> _store = [];
  Object? insertError;

  @override
  Future<void> insert(PendingReportModel report) async {
    if (insertError != null) throw insertError!;
    _store.add(report);
  }

  @override
  Future<List<PendingReportModel>> getAll() async => List.unmodifiable(_store);

  @override
  Future<List<PendingReportModel>> getByStatus(SyncStatus status) async =>
      _store.where((r) => r.syncStatus == status).toList();

  @override
  Future<void> updateStatus(
    String localId,
    SyncStatus status, {
    int? serverId,
    String? error,
  }) async {
    final idx = _store.indexWhere((r) => r.localId == localId);
    if (idx == -1) return;
    final old = _store[idx];
    _store[idx] = PendingReportModel(
      localId: old.localId,
      imagePath: old.imagePath,
      latitude: old.latitude,
      longitude: old.longitude,
      description: old.description,
      address: old.address,
      syncStatus: status,
      serverId: serverId ?? old.serverId,
      syncError: error ?? (status == SyncStatus.syncing ? null : old.syncError),
      createdAt: old.createdAt,
    );
  }

  @override
  Future<void> deleteAll() async => _store.clear();
}

// ── Helpers ────────────────────────────────────────────────────────────────

_FakeLocalDataSource _local() => _FakeLocalDataSource();

// ── Tests ──────────────────────────────────────────────────────────────────

void main() {
  group('PendingReportModel', () {
    test('round-trips through toMap / fromMap', () {
      final original = PendingReportModel(
        localId: 'abc-123',
        imagePath: '/tmp/photo.jpg',
        latitude: -12.0464,
        longitude: -77.0428,
        description: 'Bache grande en la calzada',
        address: 'Av. 27 de Febrero 123',
        city: 'Santo Domingo',
        province: 'Distrito Nacional',
        syncStatus: SyncStatus.pending,
        createdAt: DateTime(2025, 1, 15, 10, 30),
      );

      final map = original.toMap();
      final restored = PendingReportModel.fromMap(map);

      expect(restored.localId, original.localId);
      expect(restored.imagePath, original.imagePath);
      expect(restored.latitude, original.latitude);
      expect(restored.longitude, original.longitude);
      expect(restored.description, original.description);
      expect(restored.address, original.address);
      expect(restored.city, original.city);
      expect(restored.province, original.province);
      expect(restored.syncStatus, original.syncStatus);
      expect(restored.serverId, isNull);
      expect(restored.syncError, isNull);
      expect(restored.createdAt, original.createdAt);
    });

    test('fromMap uses pending as fallback for unknown sync_status', () {
      final map = {
        'local_id': 'x',
        'image_path': '/p.jpg',
        'latitude': 0.0,
        'longitude': 0.0,
        'description': 'd',
        'address': null,
        'sync_status': 'totally_unknown',
        'server_id': null,
        'sync_error': null,
        'created_at': DateTime(2025).toIso8601String(),
      };

      final model = PendingReportModel.fromMap(map);
      expect(model.syncStatus, SyncStatus.pending);
    });
  });

  group('FakeLocalDataSource', () {
    test('insert and getAll', () async {
      final ds = _local();
      final model = PendingReportModel(
        localId: 'id-1',
        imagePath: '/img.jpg',
        latitude: 1.0,
        longitude: 2.0,
        description: 'test',
        syncStatus: SyncStatus.pending,
        createdAt: DateTime.now(),
      );
      await ds.insert(model);
      final all = await ds.getAll();
      expect(all.length, 1);
      expect(all.first.localId, 'id-1');
    });

    test('getByStatus filters correctly', () async {
      final ds = _local();
      Future<void> add(String id, SyncStatus s) async => ds.insert(
            PendingReportModel(
              localId: id,
              imagePath: '/img.jpg',
              latitude: 0,
              longitude: 0,
              description: 'd',
              syncStatus: s,
              createdAt: DateTime.now(),
            ),
          );

      await add('a', SyncStatus.pending);
      await add('b', SyncStatus.synced);
      await add('c', SyncStatus.failed);

      final pending = await ds.getByStatus(SyncStatus.pending);
      expect(pending.map((r) => r.localId), ['a']);

      final failed = await ds.getByStatus(SyncStatus.failed);
      expect(failed.map((r) => r.localId), ['c']);
    });

    test('updateStatus changes sync_status field', () async {
      final ds = _local();
      await ds.insert(
        PendingReportModel(
          localId: 'z',
          imagePath: '/img.jpg',
          latitude: 0,
          longitude: 0,
          description: 'd',
          syncStatus: SyncStatus.pending,
          createdAt: DateTime.now(),
        ),
      );

      await ds.updateStatus('z', SyncStatus.synced, serverId: 99);

      final all = await ds.getAll();
      expect(all.first.syncStatus, SyncStatus.synced);
      expect(all.first.serverId, 99);
    });
  });
}
