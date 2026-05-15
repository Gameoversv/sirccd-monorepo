import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';

sealed class ReportHistoryState extends Equatable {
  const ReportHistoryState();
}

final class ReportHistoryInitial extends ReportHistoryState {
  const ReportHistoryInitial();

  @override
  List<Object?> get props => [];
}

final class ReportHistoryLoading extends ReportHistoryState {
  const ReportHistoryLoading();

  @override
  List<Object?> get props => [];
}

final class ReportHistoryLoaded extends ReportHistoryState {
  const ReportHistoryLoaded({
    required this.reports,
    required this.activeFilter,
    required this.hasMore,
    required this.isLoadingMore,
  });

  final List<UserReport> reports;
  final ReportStatus? activeFilter;
  final bool hasMore;
  final bool isLoadingMore;

  ReportHistoryLoaded copyWith({
    List<UserReport>? reports,
    ReportStatus? Function()? activeFilter,
    bool? hasMore,
    bool? isLoadingMore,
  }) =>
      ReportHistoryLoaded(
        reports: reports ?? this.reports,
        activeFilter:
            activeFilter != null ? activeFilter() : this.activeFilter,
        hasMore: hasMore ?? this.hasMore,
        isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      );

  @override
  List<Object?> get props => [reports, activeFilter, hasMore, isLoadingMore];
}

final class ReportHistoryError extends ReportHistoryState {
  const ReportHistoryError(this.message);

  final String message;

  @override
  List<Object?> get props => [message];
}
