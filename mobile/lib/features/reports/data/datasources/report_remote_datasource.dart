import 'package:dio/dio.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';

abstract interface class ReportRemoteDataSource {
  Future<int> submitReport(PendingReport report, String token);
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
      'lat': report.latitude,
      'lng': report.longitude,
      if (report.description != null && report.description!.isNotEmpty)
        'description': report.description,
      if (report.address != null && report.address!.isNotEmpty)
        'address': report.address,
      if (report.city != null && report.city!.isNotEmpty) 'city': report.city,
      if (report.province != null && report.province!.isNotEmpty)
        'province': report.province,
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
}
