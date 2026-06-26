import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';

final class DeleteAllLocalReportsUseCase {
  const DeleteAllLocalReportsUseCase(this._repository);

  final ReportRepository _repository;

  Future<void> call() => _repository.deleteAllLocal();
}
