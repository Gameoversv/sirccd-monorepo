import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';
import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';

class GetReportDetailUseCase {
  const GetReportDetailUseCase(this._repository);

  final ReportRepository _repository;

  Future<UserReport> call(int id) => _repository.getReportDetail(id);
}
