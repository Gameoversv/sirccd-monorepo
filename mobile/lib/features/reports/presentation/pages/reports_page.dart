import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_state.dart';
import 'package:sirccd_mobile/features/reports/presentation/widgets/pending_report_card.dart';
import 'package:sirccd_mobile/features/reports/presentation/widgets/sync_status_banner.dart';
import 'package:sirccd_mobile/presentation/router/app_router.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class ReportsPage extends StatelessWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => di<ReportsCubit>()..init(),
      child: const _ReportsView(),
    );
  }
}

Future<void> _confirmDeleteAll(BuildContext context) async {
  final cubit = context.read<ReportsCubit>();
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('Borrar reportes locales'),
      content: const Text(
        '¿Eliminar todos los reportes pendientes del dispositivo? '
        'Esta acción no se puede deshacer.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(ctx).pop(true),
          style: FilledButton.styleFrom(
            backgroundColor: AppColors.error,
          ),
          child: const Text('Eliminar'),
        ),
      ],
    ),
  );
  if (confirmed == true) {
    await cubit.deleteAllLocal();
  }
}

class _ReportsView extends StatelessWidget {
  const _ReportsView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis reportes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_rounded),
            tooltip: 'Borrar todos',
            onPressed: () => _confirmDeleteAll(context),
          ),
          IconButton(
            icon: const Icon(Icons.history_rounded),
            tooltip: 'Historial',
            onPressed: () => context.push(AppRoutes.reportHistory),
          ),
        ],
      ),
      body: BlocBuilder<ReportsCubit, ReportsState>(
        builder: (context, state) {
          return switch (state) {
            ReportsInitial() =>
              const Center(child: CircularProgressIndicator()),
            ReportsError(:final message) => _ErrorBody(message: message),
            ReportsLoaded() => _LoadedBody(
                state: state,
                onRetry: context.read<ReportsCubit>().retryFailed,
              ),
          };
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(AppRoutes.newReport),
        icon: const Icon(Icons.add_a_photo_rounded),
        label: const Text('Nuevo reporte'),
      ),
    );
  }
}

class _LoadedBody extends StatelessWidget {
  const _LoadedBody({required this.state, required this.onRetry});

  final ReportsLoaded state;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SyncStatusBanner(
          pendingCount: state.pendingCount,
          failedCount: state.failedCount,
          isSyncing: state.isSyncing,
          isOnline: state.isOnline,
          onRetry: onRetry,
        ),
        Expanded(
          child: state.reports.isEmpty
              ? _EmptyState(isOnline: state.isOnline)
              : ListView.builder(
                  padding: const EdgeInsets.only(top: 8, bottom: 96),
                  itemCount: state.reports.length,
                  itemBuilder: (_, i) =>
                      PendingReportCard(report: state.reports[i]),
                ),
        ),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.isOnline});

  final bool isOnline;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.report_problem_outlined,
            size: 64,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'Sin reportes aún',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Pulsa + para crear tu primer reporte.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          if (!isOnline) ...[
            const SizedBox(height: 12),
            Chip(
              avatar: const Icon(Icons.wifi_off_rounded,
                  size: 16, color: AppColors.warning),
              label: const Text('Sin conexión — se sincronizará al reconectar'),
              backgroundColor: AppColors.warningContainer,
            ),
          ],
        ],
      ),
    );
  }
}

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline_rounded,
                size: 48, color: AppColors.error),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}
