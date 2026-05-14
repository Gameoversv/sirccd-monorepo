import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';

final class GetAllReportsUseCase {
  const GetAllReportsUseCase(this._repository);

  final ReportRepository _repository;

  Stream<List<PendingReport>> call() => _repository.watchAllReports();
}
