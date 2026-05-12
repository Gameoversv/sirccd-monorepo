import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:sirccd_mobile/core/services/permission_service.dart';
import 'package:sirccd_mobile/presentation/router/app_router.dart';

class PermissionRationalePage extends StatefulWidget {
  const PermissionRationalePage({super.key});

  @override
  State<PermissionRationalePage> createState() =>
      _PermissionRationalePageState();
}

class _PermissionRationalePageState extends State<PermissionRationalePage> {
  final _service = GetIt.instance<PermissionService>();

  PermissionStatus? _locationStatus;
  PermissionStatus? _cameraStatus;
  bool _initializing = true;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    final loc = await _service.locationStatus();
    final cam = await _service.cameraStatus();
    if (!mounted) return;

    if (loc.isGranted && cam.isGranted) {
      context.go(AppRoutes.home);
      return;
    }

    setState(() {
      _locationStatus = loc;
      _cameraStatus = cam;
      _initializing = false;
    });
  }

  Future<void> _requestLocation() async {
    final status = await _service.requestLocation();
    if (!mounted) return;
    setState(() => _locationStatus = status);
    _autoAdvance();
  }

  Future<void> _requestCamera() async {
    final status = await _service.requestCamera();
    if (!mounted) return;
    setState(() => _cameraStatus = status);
    _autoAdvance();
  }

  void _autoAdvance() {
    if ((_locationStatus?.isGranted ?? false) &&
        (_cameraStatus?.isGranted ?? false)) {
      context.go(AppRoutes.home);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_initializing) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.shield_outlined, size: 48, color: cs.primary),
              const SizedBox(height: 16),
              Text('Permisos necesarios', style: theme.textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(
                'SIRCCD necesita los siguientes permisos para funcionar correctamente.',
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: cs.onSurfaceVariant),
              ),
              const SizedBox(height: 32),
              _PermissionCard(
                icon: Icons.location_on_outlined,
                title: 'Ubicación GPS',
                description:
                    'Para registrar exactamente dónde ocurre el daño vial.',
                status: _locationStatus,
                onRequest: _requestLocation,
                onSettings: _service.openSettings,
              ),
              const SizedBox(height: 16),
              _PermissionCard(
                icon: Icons.camera_alt_outlined,
                title: 'Cámara',
                description:
                    'Para capturar fotos como evidencia del daño reportado.',
                status: _cameraStatus,
                onRequest: _requestCamera,
                onSettings: _service.openSettings,
              ),
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => context.go(AppRoutes.home),
                  child: const Text('Continuar sin permisos'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PermissionCard extends StatelessWidget {
  const _PermissionCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.status,
    required this.onRequest,
    required this.onSettings,
  });

  final IconData icon;
  final String title;
  final String description;
  final PermissionStatus? status;
  final VoidCallback onRequest;
  final VoidCallback onSettings;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final granted = status?.isGranted ?? false;
    final permanentlyDenied = status?.isPermanentlyDenied ?? false;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 32, color: cs.primary),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(title, style: theme.textTheme.titleSmall),
                      const SizedBox(width: 8),
                      _StatusBadge(
                        granted: granted,
                        permanentlyDenied: permanentlyDenied,
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: cs.onSurfaceVariant),
                  ),
                  if (!granted) ...[
                    const SizedBox(height: 8),
                    TextButton(
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: const Size(0, 32),
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      onPressed: permanentlyDenied ? onSettings : onRequest,
                      child: Text(
                        permanentlyDenied
                            ? 'Abrir configuración'
                            : 'Conceder acceso',
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({
    required this.granted,
    required this.permanentlyDenied,
  });

  final bool granted;
  final bool permanentlyDenied;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final (label, color) = granted
        ? ('Concedido', Colors.green)
        : permanentlyDenied
            ? ('Denegado', cs.error)
            : ('Pendiente', Colors.orange);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
