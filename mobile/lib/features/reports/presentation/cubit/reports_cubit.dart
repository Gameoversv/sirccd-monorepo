import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/core/services/connectivity_service.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/create_pending_report_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/get_all_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/sync_pending_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_state.dart';

final class ReportsCubit extends Cubit<ReportsState> {
  ReportsCubit(
    this._createReport,
    this._getAllReports,
    this._syncReports,
    this._connectivity,
  ) : super(const ReportsInitial());

  final CreatePendingReportUseCase _createReport;
  final GetAllReportsUseCase _getAllReports;
  final SyncPendingReportsUseCase _syncReports;
  final ConnectivityService _connectivity;

  StreamSubscription<List<PendingReport>>? _reportsSub;
  StreamSubscription<bool>? _connectivitySub;
  bool _isSyncing = false;
  bool _isOnline = false;

  Future<void> init() async {
    _isOnline = await _connectivity.isConnected();

    _reportsSub = _getAllReports().listen((reports) {
      emit(
        ReportsLoaded(
          reports: reports,
          isSyncing: _isSyncing,
          isOnline: _isOnline,
        ),
      );
    });

    _connectivitySub = _connectivity.isConnectedStream.listen((online) async {
      _isOnline = online;
      final current = state;
      if (current is ReportsLoaded) {
        emit(current.copyWith(isOnline: online));
      }
      if (online) await _sync();
    });

    if (_isOnline) await _sync();
  }

  Future<void> create({
    required String imagePath,
    required double latitude,
    required double longitude,
    String? description,
    String? address,
    String? city,
    String? province,
  }) async {
    try {
      await _createReport(
        CreateReportParams(
          imagePath: imagePath,
          latitude: latitude,
          longitude: longitude,
          description: description,
          address: address,
          city: city,
          province: province,
        ),
      );
    } catch (e) {
      emit(ReportsError('No se pudo guardar el reporte: $e'));
    }
  }

  Future<void> retryFailed() async {
    if (_isOnline) await _sync();
  }

  Future<void> _sync() async {
    if (_isSyncing) return;
    _isSyncing = true;
    final current = state;
    if (current is ReportsLoaded) emit(current.copyWith(isSyncing: true));
    try {
      await _syncReports();
    } finally {
      _isSyncing = false;
      final updated = state;
      if (updated is ReportsLoaded) emit(updated.copyWith(isSyncing: false));
    }
  }

  @override
  Future<void> close() {
    _reportsSub?.cancel();
    _connectivitySub?.cancel();
    return super.close();
  }
}
