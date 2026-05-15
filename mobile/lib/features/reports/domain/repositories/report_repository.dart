import 'package:sirccd_mobile/features/reports/domain/entities/damage_type.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/paginated_reports.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/severity_level.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';

abstract interface class ReportRepository {
  Future<PendingReport> createPendingReport({
    required String imagePath,
    required double latitude,
    required double longitude,
    String? description,
    String? address,
    String? city,
    String? province,
  });

  Stream<List<PendingReport>> watchAllReports();

  Future<void> syncPendingReports();

  Future<PaginatedReports> getUserReports({
    int page = 1,
    int perPage = 20,
    ReportStatus? status,
    DamageType? damageType,
    SeverityLevel? severity,
    String? search,
    String sortOrder = 'desc',
  });

  Future<UserReport> getReportDetail(int id);
}
