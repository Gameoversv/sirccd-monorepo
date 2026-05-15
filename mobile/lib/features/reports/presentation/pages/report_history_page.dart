import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_history_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_history_state.dart';
import 'package:sirccd_mobile/features/reports/presentation/widgets/report_filter_bar.dart';
import 'package:sirccd_mobile/features/reports/presentation/widgets/user_report_card.dart';
import 'package:sirccd_mobile/presentation/router/app_router.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class ReportHistoryPage extends StatelessWidget {
  const ReportHistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => di<ReportHistoryCubit>()..load(),
      child: const _ReportHistoryView(),
    );
  }
}

class _ReportHistoryView extends StatelessWidget {
  const _ReportHistoryView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Historial de reportes')),
      body: BlocBuilder<ReportHistoryCubit, ReportHistoryState>(
        builder: (context, state) => switch (state) {
          ReportHistoryInitial() ||
          ReportHistoryLoading() =>
            const Center(child: CircularProgressIndicator()),
          ReportHistoryError(:final message) => _ErrorBody(
              message: message,
              onRetry: context.read<ReportHistoryCubit>().refresh,
            ),
          ReportHistoryLoaded() => _LoadedBody(state: state),
        },
      ),
    );
  }
}

class _LoadedBody extends StatefulWidget {
  const _LoadedBody({required this.state});

  final ReportHistoryLoaded state;

  @override
  State<_LoadedBody> createState() => _LoadedBodyState();
}

class _LoadedBodyState extends State<_LoadedBody> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    final pos = _scrollController.position;
    if (pos.pixels >= pos.maxScrollExtent - 200) {
      context.read<ReportHistoryCubit>().loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    return Column(
      children: [
        ReportFilterBar(
          activeFilter: state.activeFilter,
          onFilterChanged: context.read<ReportHistoryCubit>().setFilter,
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: context.read<ReportHistoryCubit>().refresh,
            child: state.reports.isEmpty
                ? const _EmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.only(top: 4, bottom: 24),
                    itemCount:
                        state.reports.length + (state.isLoadingMore ? 1 : 0),
                    itemBuilder: (context, i) {
                      if (i == state.reports.length) {
                        return const Padding(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          child: Center(child: CircularProgressIndicator()),
                        );
                      }
                      final report = state.reports[i];
                      return UserReportCard(
                        report: report,
                        onTap: () => context.push(
                          AppRoutes.reportDetail(report.id),
                        ),
                      );
                    },
                  ),
          ),
        ),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        SizedBox(height: MediaQuery.of(context).size.height * 0.25),
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.history_rounded,
              size: 64,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'Sin reportes',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'No se encontraron reportes con el filtro seleccionado.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ],
    );
  }
}

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.error_outline_rounded,
              size: 48,
              color: AppColors.error,
            ),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }
}

