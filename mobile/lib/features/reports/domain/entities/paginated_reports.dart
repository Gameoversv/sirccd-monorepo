import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';

class PaginatedReports extends Equatable {
  const PaginatedReports({
    required this.items,
    required this.total,
    required this.page,
    required this.perPage,
    required this.totalPages,
  });

  final List<UserReport> items;
  final int total;
  final int page;
  final int perPage;
  final int totalPages;

  bool get hasMore => page < totalPages;

  @override
  List<Object?> get props => [items, total, page, perPage, totalPages];
}
