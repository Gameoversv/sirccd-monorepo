import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';

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
}
