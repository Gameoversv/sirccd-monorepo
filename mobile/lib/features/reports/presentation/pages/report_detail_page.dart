import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/report_status.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/severity_level.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/user_report.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_detail_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_detail_state.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class ReportDetailPage extends StatelessWidget {
  const ReportDetailPage({super.key, required this.reportId});

  final int reportId;

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => di<ReportDetailCubit>()..load(reportId),
      child: const _ReportDetailView(),
    );
  }
}

class _ReportDetailView extends StatelessWidget {
  const _ReportDetailView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocBuilder<ReportDetailCubit, ReportDetailState>(
        builder: (context, state) => switch (state) {
          ReportDetailInitial() ||
          ReportDetailLoading() => const _LoadingScaffold(),
          ReportDetailError(:final message) => _ErrorScaffold(message: message),
          ReportDetailLoaded(:final report) => _DetailScaffold(report: report),
        },
      ),
    );
  }
}

class _LoadingScaffold extends StatelessWidget {
  const _LoadingScaffold();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(),
      body: const Center(child: CircularProgressIndicator()),
    );
  }
}

class _ErrorScaffold extends StatelessWidget {
  const _ErrorScaffold({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detalle')),
      body: Center(
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
              Text(message, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailScaffold extends StatelessWidget {
  const _DetailScaffold({required this.report});

  final UserReport report;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        _ImageSliverAppBar(report: report),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _StatusRow(report: report),
                const SizedBox(height: 20),
                if (report.description != null &&
                    report.description!.isNotEmpty) ...[
                  _SectionLabel('Descripción'),
                  const SizedBox(height: 6),
                  Text(
                    report.description!,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 20),
                ],
                if (report.annotatedImageUrl != null &&
                    report.annotatedImageUrl!.isNotEmpty) ...[
                  _SectionLabel('Resultado ML'),
                  const SizedBox(height: 8),
                  _DetectionImageSection(report: report),
                  const SizedBox(height: 20),
                ],
                _SectionLabel('Ubicación'),
                const SizedBox(height: 8),
                _LocationSection(report: report),
                const SizedBox(height: 20),
                _SectionLabel('Detalles del análisis'),
                const SizedBox(height: 8),
                _AnalysisSection(report: report),
                if (report.status == ReportStatus.rejected &&
                    report.rejectionReason != null) ...[
                  const SizedBox(height: 20),
                  _RejectionSection(reason: report.rejectionReason!),
                ],
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ImageSliverAppBar extends StatelessWidget {
  const _ImageSliverAppBar({required this.report});

  final UserReport report;

  @override
  Widget build(BuildContext context) {
    return SliverAppBar(
      expandedHeight: 280,
      pinned: true,
      title: Text('Reporte #${report.id}'),
      flexibleSpace: FlexibleSpaceBar(
        background: Image.network(
          report.imageUrl,
          fit: BoxFit.cover,
          loadingBuilder: (_, child, progress) => progress == null
              ? child
              : Container(
                  color: AppColors.surfaceVariant,
                  child: const Center(child: CircularProgressIndicator()),
                ),
          errorBuilder: (_, __, ___) => Container(
            color: AppColors.surfaceVariant,
            child: const Icon(
              Icons.image_not_supported_outlined,
              size: 48,
              color: AppColors.onSurfaceVariant,
            ),
          ),
        ),
      ),
    );
  }
}

class _DetectionImageSection extends StatelessWidget {
  const _DetectionImageSection({required this.report});

  final UserReport report;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final panels = [
          _ReportImagePanel(
            title: 'Anotacion ML',
            url: report.annotatedImageUrl!,
            icon: Icons.auto_awesome_rounded,
          ),
          _ReportImagePanel(
            title: 'Original',
            url: report.imageUrl,
            icon: Icons.image_outlined,
          ),
        ];

        if (constraints.maxWidth >= 560) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: panels[0]),
              const SizedBox(width: 12),
              Expanded(child: panels[1]),
            ],
          );
        }

        return Column(
          children: [panels[0], const SizedBox(height: 12), panels[1]],
        );
      },
    );
  }
}

class _ReportImagePanel extends StatelessWidget {
  const _ReportImagePanel({
    required this.title,
    required this.url,
    required this.icon,
  });

  final String title;
  final String url;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: AspectRatio(
        aspectRatio: 4 / 3,
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.network(
              url,
              fit: BoxFit.cover,
              loadingBuilder: (_, child, progress) => progress == null
                  ? child
                  : Container(
                      color: AppColors.surfaceVariant,
                      child: const Center(child: CircularProgressIndicator()),
                    ),
              errorBuilder: (_, __, ___) => Container(
                color: AppColors.surfaceVariant,
                child: const Icon(
                  Icons.image_not_supported_outlined,
                  size: 40,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
            ),
            Positioned(
              left: 8,
              bottom: 8,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.62),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 5,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(icon, size: 14, color: Colors.white),
                      const SizedBox(width: 5),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.report});

  final UserReport report;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        _Badge(
          label: report.status.label,
          color: _statusColor(report.status),
          icon: _statusIcon(report.status),
        ),
        if (report.damageType != null)
          _Badge(
            label: report.damageType!.label,
            color: AppColors.surfaceVariant,
            icon: Icons.warning_amber_rounded,
          ),
        if (report.severity != null)
          _Badge(
            label: 'Severidad: ${report.severity!.label}',
            color: _severityColor(report.severity!),
            icon: Icons.bar_chart_rounded,
          ),
        if (report.confidence != null)
          _Badge(
            label:
                'Confianza: ${(report.confidence! * 100).toStringAsFixed(0)}%',
            color: AppColors.primaryContainer,
            icon: Icons.auto_awesome_rounded,
          ),
        Text(
          _formatDate(report.createdAt),
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Color _statusColor(ReportStatus s) => switch (s) {
    ReportStatus.pending => AppColors.warningContainer,
    ReportStatus.processing => AppColors.primaryContainer,
    ReportStatus.approved => const Color(0xFFDCFCE7),
    ReportStatus.rejected => AppColors.errorContainer,
  };

  IconData _statusIcon(ReportStatus s) => switch (s) {
    ReportStatus.pending => Icons.schedule_rounded,
    ReportStatus.processing => Icons.sync_rounded,
    ReportStatus.approved => Icons.check_circle_outline_rounded,
    ReportStatus.rejected => Icons.cancel_outlined,
  };

  Color _severityColor(SeverityLevel s) => switch (s) {
    SeverityLevel.baja => const Color(0xFFDCFCE7),
    SeverityLevel.media => AppColors.warningContainer,
    SeverityLevel.alta => AppColors.errorContainer,
  };

  String _formatDate(DateTime dt) =>
      '${dt.day.toString().padLeft(2, '0')}/'
      '${dt.month.toString().padLeft(2, '0')}/'
      '${dt.year}  '
      '${dt.hour.toString().padLeft(2, '0')}:'
      '${dt.minute.toString().padLeft(2, '0')}';
}

class _LocationSection extends StatelessWidget {
  const _LocationSection({required this.report});

  final UserReport report;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (report.address != null && report.address!.isNotEmpty) ...[
          Row(
            children: [
              const Icon(
                Icons.location_on_outlined,
                size: 16,
                color: AppColors.outline,
              ),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  [
                    report.address,
                    report.city,
                    report.province,
                  ].whereType<String>().join(', '),
                  style: theme.textTheme.bodyMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
        ],
        Text(
          '${report.latitude.toStringAsFixed(6)}, ${report.longitude.toStringAsFixed(6)}',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
            fontFamily: 'monospace',
          ),
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: SizedBox(
            height: 180,
            child: FlutterMap(
              options: MapOptions(
                initialCenter: LatLng(report.latitude, report.longitude),
                initialZoom: 15,
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.none,
                ),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.sirccd.mobile',
                ),
                MarkerLayer(
                  markers: [
                    Marker(
                      point: LatLng(report.latitude, report.longitude),
                      child: const Icon(
                        Icons.location_pin,
                        color: AppColors.error,
                        size: 36,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _AnalysisSection extends StatelessWidget {
  const _AnalysisSection({required this.report});

  final UserReport report;

  @override
  Widget build(BuildContext context) {
    final rows = <(String, String)>[
      if (report.damageType != null) ('Tipo de daño', report.damageType!.label),
      if (report.severity != null) ('Severidad', report.severity!.label),
      if (report.confidence != null)
        (
          'Confianza del modelo',
          '${(report.confidence! * 100).toStringAsFixed(1)}%',
        ),
      if (report.detectionCount != null)
        ('Detecciones ML', report.detectionCount.toString()),
      if (report.modelVersion != null && report.modelVersion!.isNotEmpty)
        ('Modelo', report.modelVersion!),
      if (report.modelPrecision != null)
        ('Precision validacion', _formatPercent(report.modelPrecision!)),
      if (report.modelRecall != null)
        ('Recall validacion', _formatPercent(report.modelRecall!)),
      if (report.modelMap50 != null)
        ('mAP50', _formatPercent(report.modelMap50!)),
      if (report.annotatedImageUrl != null &&
          report.annotatedImageUrl!.isNotEmpty)
        ('Anotacion ML', 'Disponible'),
      ('Estado', report.status.label),
      if (report.reviewedAt != null)
        (
          'Revisado el',
          '${report.reviewedAt!.day.toString().padLeft(2, '0')}/'
              '${report.reviewedAt!.month.toString().padLeft(2, '0')}/'
              '${report.reviewedAt!.year}',
        ),
    ];

    if (rows.isEmpty) {
      return Text(
        'Análisis no disponible',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      );
    }

    return Column(
      children: rows
          .map((row) => _InfoRow(label: row.$1, value: row.$2))
          .toList(),
    );
  }

  String _formatPercent(double value) {
    final percent = value <= 1 ? value * 100 : value;
    return '${percent.toStringAsFixed(1)}%';
  }
}

class _RejectionSection extends StatelessWidget {
  const _RejectionSection({required this.reason});

  final String reason;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.errorContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline_rounded,
            size: 16,
            color: AppColors.error,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Motivo de rechazo',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: AppColors.onErrorContainer,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  reason,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.onErrorContainer,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: Theme.of(
        context,
      ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label, required this.color, required this.icon});

  final String label;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: AppColors.onSurfaceVariant),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: AppColors.onSurface,
            ),
          ),
        ],
      ),
    );
  }
}
