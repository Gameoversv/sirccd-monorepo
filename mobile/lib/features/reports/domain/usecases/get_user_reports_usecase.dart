import 'package:sirccd_mobile/features/reports/domain/entities/damage_type.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/paginated_reports.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/severity_level.dart';
import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';

class GetUserReportsUseCase {
  const GetUserReportsUseCase(this._repository);

  final ReportRepository _repository;

  Future<PaginatedReports> call({
    int page = 1,
    int perPage = 20,
    ReportStatus? status,
    DamageType? damageType,
    SeverityLevel? severity,
    String? search,
    String sortOrder = 'desc',
  }) =>
      _repository.getUserReports(
        page: page,
        perPage: perPage,
        status: status,
        damageType: damageType,
        severity: severity,
        search: search,
        sortOrder: sortOrder,
      );
}
