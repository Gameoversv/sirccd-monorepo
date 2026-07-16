import 'package:dio/dio.dart';
import 'package:sirccd_mobile/features/reports/data/models/user_report_model.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/damage_type.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/paginated_reports.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/severity_level.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';

abstract interface class ReportRemoteDataSource {
  Future<int> submitReport(PendingReport report, String token);

  Future<PaginatedReports> getUserReports({
    required String token,
    int page = 1,
    int perPage = 20,
    ReportStatus? status,
    DamageType? damageType,
    SeverityLevel? severity,
    String? search,
    String sortOrder = 'desc',
  });

  Future<UserReport> getReportDetail({required int id, required String token});
}

final class ReportRemoteDataSourceImpl implements ReportRemoteDataSource {
  const ReportRemoteDataSourceImpl(this._dio);

  final Dio _dio;

  @override
  Future<int> submitReport(PendingReport report, String token) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(
        report.imagePath,
        filename: 'report.jpg',
      ),
      'latitude': report.latitude,
      'longitude': report.longitude,
      if (report.description != null && report.description!.isNotEmpty)
        'description': report.description,
      if (report.address != null && report.address!.isNotEmpty)
        'address': report.address,
      if (report.city != null && report.city!.isNotEmpty) 'city': report.city,
      if (report.province != null && report.province!.isNotEmpty)
        'province': report.province,
      if (report.focalScaleFactor != null)
        'focal_scale_factor': report.focalScaleFactor,
    });

    final response = await _dio.post<Map<String, dynamic>>(
      '/reportes',
      data: formData,
      options: Options(
        headers: {'Authorization': 'Bearer $token'},
        contentType: 'multipart/form-data',
      ),
    );

    return (response.data?['id'] as num).toInt();
  }

  @override
  Future<PaginatedReports> getUserReports({
    required String token,
    int page = 1,
    int perPage = 20,
    ReportStatus? status,
    DamageType? damageType,
    SeverityLevel? severity,
    String? search,
    String sortOrder = 'desc',
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reportes',
      queryParameters: {
        'page': page,
        'per_page': perPage,
        if (status != null) 'status': status.name,
        if (damageType != null) 'damage_type': damageType.name,
        if (severity != null) 'severity': severity.name,
        if (search != null && search.isNotEmpty) 'search': search,
        'sort_order': sortOrder,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );

    final data = response.data!;
    final items = (data['items'] as List)
        .cast<Map<String, dynamic>>()
        .map(UserReportModel.fromJson)
        .toList();

    return PaginatedReports(
      items: items,
      total: (data['total'] as num).toInt(),
      page: (data['page'] as num).toInt(),
      perPage: (data['per_page'] as num).toInt(),
      totalPages: (data['total_pages'] as num).toInt(),
    );
  }

  @override
  Future<UserReport> getReportDetail({
    required int id,
    required String token,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reportes/$id',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );

    return UserReportModel.fromJson(response.data!);
  }
}
