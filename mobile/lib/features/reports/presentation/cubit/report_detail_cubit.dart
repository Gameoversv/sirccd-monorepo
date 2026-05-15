import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/get_report_detail_usecase.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_detail_state.dart';

class ReportDetailCubit extends Cubit<ReportDetailState> {
  ReportDetailCubit(this._getDetail) : super(const ReportDetailInitial());

  final GetReportDetailUseCase _getDetail;

  Future<void> load(int id) async {
    emit(const ReportDetailLoading());
    try {
      final report = await _getDetail(id);
      emit(ReportDetailLoaded(report));
    } on Exception catch (e) {
      final msg = e.toString();
      if (msg.contains('404') || msg.contains('Not Found')) {
        emit(const ReportDetailError('Reporte no encontrado'));
      } else if (msg.contains('No autenticado')) {
        emit(const ReportDetailError('Sesión expirada'));
      } else {
        emit(const ReportDetailError('Error al cargar el reporte'));
      }
    }
  }
}
