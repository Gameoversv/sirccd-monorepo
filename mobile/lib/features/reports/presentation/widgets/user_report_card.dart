import 'package:flutter/material.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class UserReportCard extends StatelessWidget {
  const UserReportCard({
    super.key,
    required this.report,
    required this.onTap,
  });

  final UserReport report;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _NetworkThumbnail(url: report.imageUrl),
            const SizedBox(width: 12),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            report.description ?? _fallbackTitle(report),
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        _StatusBadge(status: report.status),
                      ],
                    ),
                    if (report.damageType != null ||
                        report.severity != null) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          if (report.damageType != null)
                            _MetaChip(
                              label: report.damageType!.label,
                              icon: Icons.warning_amber_rounded,
                            ),
                          if (report.damageType != null &&
                              report.severity != null)
                            const SizedBox(width: 4),
                          if (report.severity != null)
                            _MetaChip(
                              label: report.severity!.label,
                              icon: Icons.bar_chart_rounded,
                            ),
                        ],
                      ),
                    ],
                    const SizedBox(height: 4),
                    Text(
                      _formatLocation(report),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _formatDate(report.createdAt),
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.only(right: 8, top: 16),
              child: Icon(
                Icons.chevron_right_rounded,
                size: 20,
                color: AppColors.outline,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _fallbackTitle(UserReport r) {
    if (r.damageType != null) return r.damageType!.label;
    return 'Reporte #${r.id}';
  }

  String _formatLocation(UserReport r) {
    if (r.address != null && r.address!.isNotEmpty) return r.address!;
    return '${r.latitude.toStringAsFixed(5)}, ${r.longitude.toStringAsFixed(5)}';
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 1) return 'Ahora';
    if (diff.inMinutes < 60) return 'Hace ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'Hace ${diff.inHours} h';
    if (diff.inDays < 30) {
      return 'Hace ${diff.inDays} día${diff.inDays == 1 ? '' : 's'}';
    }
    return '${dt.day}/${dt.month}/${dt.year}';
  }
}

class _NetworkThumbnail extends StatelessWidget {
  const _NetworkThumbnail({required this.url});

  final String url;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(12),
        bottomLeft: Radius.circular(12),
      ),
      child: Image.network(
        url,
        width: 80,
        height: 80,
        fit: BoxFit.cover,
        loadingBuilder: (_, child, progress) => progress == null
            ? child
            : Container(
                width: 80,
                height: 80,
                color: AppColors.surfaceVariant,
                child: const Center(
                  child: SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              ),
        errorBuilder: (_, __, ___) => Container(
          width: 80,
          height: 80,
          color: AppColors.surfaceVariant,
          child: const Icon(
            Icons.image_not_supported_outlined,
            color: AppColors.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});

  final ReportStatus status;

  @override
  Widget build(BuildContext context) {
    final (color, icon, textColor) = switch (status) {
      ReportStatus.pending => (
          AppColors.warningContainer,
          Icons.schedule_rounded,
          AppColors.statusPending,
        ),
      ReportStatus.processing => (
          AppColors.primaryContainer,
          Icons.sync_rounded,
          AppColors.statusInProgress,
        ),
      ReportStatus.approved => (
          const Color(0xFFDCFCE7),
          Icons.check_circle_outline_rounded,
          AppColors.statusResolved,
        ),
      ReportStatus.rejected => (
          AppColors.errorContainer,
          Icons.cancel_outlined,
          AppColors.statusRejected,
        ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: textColor),
          const SizedBox(width: 3),
          Text(
            status.label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.label, required this.icon});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 12, color: AppColors.outline),
        const SizedBox(width: 2),
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            color: AppColors.outline,
          ),
        ),
      ],
    );
  }
}
