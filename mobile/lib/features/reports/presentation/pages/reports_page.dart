import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
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

class _ReportsView extends StatefulWidget {
  const _ReportsView();

  @override
  State<_ReportsView> createState() => _ReportsViewState();
}

class _ReportsViewState extends State<_ReportsView> {
  bool _gettingLocation = false;

  void _showSourcePicker() {
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: AppColors.outlineVariant,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Text(
                'Agregar foto',
                style: Theme.of(ctx).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
              ),
              const SizedBox(height: 8),
              ListTile(
                leading: const CircleAvatar(
                  backgroundColor: AppColors.primaryContainer,
                  child: Icon(Icons.camera_alt_rounded, color: AppColors.primary),
                ),
                title: const Text('Tomar foto'),
                subtitle: const Text('Abrir cámara'),
                onTap: () {
                  Navigator.pop(ctx);
                  _openCamera();
                },
              ),
              ListTile(
                leading: const CircleAvatar(
                  backgroundColor: AppColors.secondaryContainer,
                  child: Icon(Icons.photo_library_rounded, color: AppColors.secondary),
                ),
                title: const Text('Elegir de galería'),
                subtitle: const Text('Seleccionar foto existente'),
                onTap: () {
                  Navigator.pop(ctx);
                  _openGallery();
                },
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _openCamera() async {
    final capture = await context.push<PhotoCapture>(AppRoutes.camera);
    if (capture == null || !mounted) return;
    context.push(AppRoutes.newReport, extra: capture);
  }

  Future<void> _openGallery() async {
    final picker = ImagePicker();
    final xFile = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 90,
    );
    if (xFile == null || !mounted) return;

    setState(() => _gettingLocation = true);

    Position? position;
    try {
      position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 8),
        ),
      );
    } catch (_) {
      // GPS unavailable — user sees warning on next page
    }

    if (!mounted) return;
    setState(() => _gettingLocation = false);

    final capture = PhotoCapture(
      imagePath: xFile.path,
      timestamp: DateTime.now(),
      orientation: DeviceOrientation.portraitUp,
      latitude: position?.latitude,
      longitude: position?.longitude,
      accuracyMeters: position?.accuracy,
    );

    if (mounted) context.push(AppRoutes.newReport, extra: capture);
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Scaffold(
          appBar: AppBar(title: const Text('Mis reportes')),
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
            onPressed: _gettingLocation ? null : _showSourcePicker,
            icon: const Icon(Icons.add_a_photo_rounded),
            label: const Text('Nuevo reporte'),
          ),
        ),
        if (_gettingLocation) _LocationLoadingOverlay(),
      ],
    );
  }
}

class _LocationLoadingOverlay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black26,
      child: Center(
        child: Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: const Padding(
            padding: EdgeInsets.symmetric(horizontal: 32, vertical: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(color: AppColors.primary),
                SizedBox(height: 16),
                Text('Obteniendo ubicación…'),
              ],
            ),
          ),
        ),
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
