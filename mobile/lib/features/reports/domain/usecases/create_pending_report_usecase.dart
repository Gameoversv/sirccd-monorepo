import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';

final class CreateReportParams extends Equatable {
  const CreateReportParams({
    required this.imagePath,
    required this.latitude,
    required this.longitude,
    this.description,
    this.address,
    this.city,
    this.province,
    this.focalScaleFactor,
  });

  final String imagePath;
  final double latitude;
  final double longitude;
  final String? description;
  final String? address;
  final String? city;
  final String? province;
  final double? focalScaleFactor;

  @override
  List<Object?> get props => [
    imagePath,
    latitude,
    longitude,
    description,
    address,
    city,
    province,
    focalScaleFactor,
  ];
}

final class CreatePendingReportUseCase {
  const CreatePendingReportUseCase(this._repository);

  final ReportRepository _repository;

  Future<PendingReport> call(CreateReportParams params) =>
      _repository.createPendingReport(
        imagePath: params.imagePath,
        latitude: params.latitude,
        longitude: params.longitude,
        description: params.description,
        address: params.address,
        city: params.city,
        province: params.province,
        focalScaleFactor: params.focalScaleFactor,
      );
}
