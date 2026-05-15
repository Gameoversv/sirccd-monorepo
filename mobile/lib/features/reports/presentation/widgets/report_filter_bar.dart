import 'package:flutter/material.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class ReportFilterBar extends StatelessWidget {
  const ReportFilterBar({
    super.key,
    required this.activeFilter,
    required this.onFilterChanged,
  });

  final ReportStatus? activeFilter;
  final ValueChanged<ReportStatus?> onFilterChanged;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        children: [
          _FilterChip(
            label: 'Todos',
            selected: activeFilter == null,
            onTap: () => onFilterChanged(null),
          ),
          const SizedBox(width: 8),
          ...ReportStatus.values.map(
            (s) => Padding(
              padding: const EdgeInsets.only(right: 8),
              child: _FilterChip(
                label: s.label,
                selected: activeFilter == s,
                color: _statusColor(s),
                onTap: () =>
                    onFilterChanged(activeFilter == s ? null : s),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _statusColor(ReportStatus status) => switch (status) {
        ReportStatus.pending => AppColors.statusPending,
        ReportStatus.processing => AppColors.statusInProgress,
        ReportStatus.approved => AppColors.statusResolved,
        ReportStatus.rejected => AppColors.statusRejected,
      };
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
    this.color,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activeColor = color ?? theme.colorScheme.primary;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        decoration: BoxDecoration(
          color: selected ? activeColor.withValues(alpha: 0.15) : Colors.transparent,
          border: Border.all(
            color: selected ? activeColor : theme.colorScheme.outlineVariant,
            width: selected ? 1.5 : 1,
          ),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: theme.textTheme.labelMedium?.copyWith(
            color: selected ? activeColor : theme.colorScheme.onSurfaceVariant,
            fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}
