import 'dart:io';

import 'package:flutter/material.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class PendingReportCard extends StatelessWidget {
  const PendingReportCard({super.key, required this.report, this.onTap});

  final PendingReport report;
  final VoidCallback? onTap;

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
            _Thumbnail(imagePath: report.imagePath),
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
                            report.description ?? 'Sin descripción',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        _SyncBadge(status: report.syncStatus),
                      ],
                    ),
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
                    if (report.syncStatus == SyncStatus.failed &&
                        report.syncError != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        report.syncError!,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: AppColors.error,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(right: 8, top: 16),
              child: Icon(
                Icons.chevron_right_rounded,
                size: 20,
                color: report.serverId != null
                    ? AppColors.outline
                    : AppColors.outline.withValues(alpha: 0.4),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatLocation(PendingReport r) {
    if (r.address != null && r.address!.isNotEmpty) return r.address!;
    return '${r.latitude.toStringAsFixed(5)}, ${r.longitude.toStringAsFixed(5)}';
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 1) return 'Ahora';
    if (diff.inMinutes < 60) return 'Hace ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'Hace ${diff.inHours} h';
    return 'Hace ${diff.inDays} día${diff.inDays == 1 ? '' : 's'}';
  }
}

class _Thumbnail extends StatelessWidget {
  const _Thumbnail({required this.imagePath});

  final String imagePath;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(12),
        bottomLeft: Radius.circular(12),
      ),
      child: Image.file(
        File(imagePath),
        width: 80,
        height: 80,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => Container(
          width: 80,
          height: 80,
          color: AppColors.surfaceVariant,
          child: const Icon(Icons.image_not_supported_outlined,
              color: AppColors.onSurfaceVariant),
        ),
      ),
    );
  }
}

class _SyncBadge extends StatelessWidget {
  const _SyncBadge({required this.status});

  final SyncStatus status;

  @override
  Widget build(BuildContext context) {
    return switch (status) {
      SyncStatus.pending => _badge(
          color: AppColors.warningContainer,
          icon: Icons.schedule_rounded,
          iconColor: AppColors.warning,
          label: 'Pendiente',
          textColor: AppColors.warning,
        ),
      SyncStatus.syncing => _badge(
          color: AppColors.primaryContainer,
          icon: Icons.sync_rounded,
          iconColor: AppColors.primary,
          label: 'Enviando',
          textColor: AppColors.primary,
        ),
      SyncStatus.synced => _badge(
          color: const Color(0xFFDCFCE7),
          icon: Icons.check_circle_outline_rounded,
          iconColor: AppColors.statusResolved,
          label: 'Enviado',
          textColor: AppColors.statusResolved,
        ),
      SyncStatus.failed => _badge(
          color: AppColors.errorContainer,
          icon: Icons.error_outline_rounded,
          iconColor: AppColors.error,
          label: 'Error',
          textColor: AppColors.error,
        ),
    };
  }

  Widget _badge({
    required Color color,
    required IconData icon,
    required Color iconColor,
    required String label,
    required Color textColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: iconColor),
          const SizedBox(width: 3),
          Text(
            label,
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
