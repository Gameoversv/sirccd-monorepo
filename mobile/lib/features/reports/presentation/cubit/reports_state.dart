import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';

sealed class ReportsState extends Equatable {
  const ReportsState();
}

final class ReportsInitial extends ReportsState {
  const ReportsInitial();

  @override
  List<Object?> get props => [];
}

final class ReportsLoaded extends ReportsState {
  const ReportsLoaded({
    required this.reports,
    required this.isSyncing,
    required this.isOnline,
  });

  final List<PendingReport> reports;
  final bool isSyncing;
  final bool isOnline;

  int get pendingCount =>
      reports.where((r) => r.syncStatus == SyncStatus.pending).length;

  int get syncingCount =>
      reports.where((r) => r.syncStatus == SyncStatus.syncing).length;

  int get failedCount =>
      reports.where((r) => r.syncStatus == SyncStatus.failed).length;

  bool get hasPendingOrSyncing => pendingCount > 0 || syncingCount > 0;

  ReportsLoaded copyWith({
    List<PendingReport>? reports,
    bool? isSyncing,
    bool? isOnline,
  }) =>
      ReportsLoaded(
        reports: reports ?? this.reports,
        isSyncing: isSyncing ?? this.isSyncing,
        isOnline: isOnline ?? this.isOnline,
      );

  @override
  List<Object?> get props => [reports, isSyncing, isOnline];
}

final class ReportsError extends ReportsState {
  const ReportsError(this.message);

  final String message;

  @override
  List<Object?> get props => [message];
}
