import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/get_user_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_history_state.dart';

class ReportHistoryCubit extends Cubit<ReportHistoryState> {
  ReportHistoryCubit(this._getUserReports)
      : super(const ReportHistoryInitial());

  final GetUserReportsUseCase _getUserReports;

  ReportStatus? _activeFilter;
  int _currentPage = 1;
  static const _perPage = 20;

  Future<void> load({ReportStatus? status}) async {
    _activeFilter = status;
    _currentPage = 1;
    emit(const ReportHistoryLoading());
    try {
      final result = await _getUserReports(
        page: 1,
        perPage: _perPage,
        status: status,
      );
      emit(ReportHistoryLoaded(
        reports: result.items,
        activeFilter: status,
        hasMore: result.hasMore,
        isLoadingMore: false,
      ));
    } on Exception catch (e) {
      emit(ReportHistoryError(_formatError(e)));
    }
  }

  Future<void> loadMore() async {
    final current = state;
    if (current is! ReportHistoryLoaded ||
        !current.hasMore ||
        current.isLoadingMore) {
      return;
    }

    emit(current.copyWith(isLoadingMore: true));
    try {
      _currentPage++;
      final result = await _getUserReports(
        page: _currentPage,
        perPage: _perPage,
        status: _activeFilter,
      );
      emit(current.copyWith(
        reports: [...current.reports, ...result.items],
        hasMore: result.hasMore,
        isLoadingMore: false,
      ));
    } on Exception {
      _currentPage--;
      final s = state;
      if (s is ReportHistoryLoaded) {
        emit(s.copyWith(isLoadingMore: false));
      }
    }
  }

  Future<void> setFilter(ReportStatus? status) => load(status: status);

  Future<void> refresh() => load(status: _activeFilter);

  String _formatError(Exception e) {
    final msg = e.toString();
    if (msg.contains('No autenticado')) return 'Sesión expirada';
    if (msg.contains('SocketException') || msg.contains('DioException')) {
      return 'Sin conexión a internet';
    }
    return 'Error al cargar reportes';
  }
}
