import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';

sealed class ReportDetailState extends Equatable {
  const ReportDetailState();
}

final class ReportDetailInitial extends ReportDetailState {
  const ReportDetailInitial();

  @override
  List<Object?> get props => [];
}

final class ReportDetailLoading extends ReportDetailState {
  const ReportDetailLoading();

  @override
  List<Object?> get props => [];
}

final class ReportDetailLoaded extends ReportDetailState {
  const ReportDetailLoaded(this.report);

  final UserReport report;

  @override
  List<Object?> get props => [report];
}

final class ReportDetailError extends ReportDetailState {
  const ReportDetailError(this.message);

  final String message;

  @override
  List<Object?> get props => [message];
}
