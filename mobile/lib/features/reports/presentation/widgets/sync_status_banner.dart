import 'package:flutter/material.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class SyncStatusBanner extends StatelessWidget {
  const SyncStatusBanner({
    super.key,
    required this.pendingCount,
    required this.failedCount,
    required this.isSyncing,
    required this.isOnline,
    required this.onRetry,
  });

  final int pendingCount;
  final int failedCount;
  final bool isSyncing;
  final bool isOnline;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    if (isSyncing) return _SyncingBanner();
    if (!isOnline && pendingCount > 0) {
      return _OfflineBanner(pendingCount: pendingCount);
    }
    if (failedCount > 0) {
      return _FailedBanner(failedCount: failedCount, onRetry: onRetry);
    }
    return const SizedBox.shrink();
  }
}

class _SyncingBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return _Banner(
      color: AppColors.primaryContainer,
      icon: const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: AppColors.primary,
        ),
      ),
      message: 'Sincronizando reportes…',
    );
  }
}

class _OfflineBanner extends StatelessWidget {
  const _OfflineBanner({required this.pendingCount});

  final int pendingCount;

  @override
  Widget build(BuildContext context) {
    final label = pendingCount == 1
        ? '1 reporte en espera'
        : '$pendingCount reportes en espera';
    return _Banner(
      color: AppColors.warningContainer,
      icon: const Icon(Icons.wifi_off_rounded, size: 18, color: AppColors.warning),
      message: 'Sin conexión · $label',
    );
  }
}

class _FailedBanner extends StatelessWidget {
  const _FailedBanner({required this.failedCount, required this.onRetry});

  final int failedCount;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final label = failedCount == 1
        ? '1 reporte no pudo enviarse'
        : '$failedCount reportes no pudieron enviarse';
    return _Banner(
      color: AppColors.errorContainer,
      icon: const Icon(Icons.error_outline_rounded, size: 18, color: AppColors.error),
      message: label,
      trailing: TextButton(
        onPressed: onRetry,
        style: TextButton.styleFrom(
          foregroundColor: AppColors.error,
          padding: const EdgeInsets.symmetric(horizontal: 8),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        child: const Text('Reintentar'),
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({
    required this.color,
    required this.icon,
    required this.message,
    this.trailing,
  });

  final Color color;
  final Widget icon;
  final String message;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: color,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          icon,
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}
