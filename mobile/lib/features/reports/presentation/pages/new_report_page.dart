import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:latlong2/latlong.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_state.dart';
import 'package:sirccd_mobile/presentation/router/app_router.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class NewReportPage extends StatefulWidget {
  const NewReportPage({super.key, this.capture});

  final PhotoCapture? capture;

  @override
  State<NewReportPage> createState() => _NewReportPageState();
}

class _NewReportPageState extends State<NewReportPage> {
  final _formKey = GlobalKey<FormState>();
  final _descriptionController = TextEditingController();
  final _addressController = TextEditingController();
  final _cityController = TextEditingController();
  final _provinceController = TextEditingController();
  bool _submitting = false;
  bool _gettingLocation = false;
  PhotoCapture? _capture;

  @override
  void initState() {
    super.initState();
    _capture = widget.capture;
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _provinceController.dispose();
    super.dispose();
  }

  bool get _hasLocation {
    final c = _capture;
    if (c == null) return false;
    return c.hasLocation &&
        c.latitude != null &&
        c.longitude != null &&
        c.latitude! >= -90 &&
        c.latitude! <= 90 &&
        c.longitude! >= -180 &&
        c.longitude! <= 180;
  }

  Future<void> _reverseGeocode(double lat, double lng) async {
    try {
      final client = HttpClient();
      final uri = Uri.parse(
        'https://nominatim.openstreetmap.org/reverse?lat=$lat&lon=$lng&format=json&accept-language=es',
      );
      final request = await client.getUrl(uri);
      request.headers.set('User-Agent', 'sirccd-mobile/1.0');
      final response = await request.close();
      final body = await response.transform(utf8.decoder).join();
      client.close();

      if (!mounted) return;
      final data = jsonDecode(body) as Map<String, dynamic>;
      final addr = data['address'] as Map<String, dynamic>?;
      if (addr == null) return;

      final road = addr['road'] as String? ?? addr['pedestrian'] as String? ?? '';
      final number = addr['house_number'] as String? ?? '';
      final street = number.isNotEmpty ? '$road $number'.trim() : road;
      final city = addr['city'] as String? ??
          addr['town'] as String? ??
          addr['village'] as String? ??
          addr['municipality'] as String? ??
          '';
      final province = addr['state'] as String? ?? addr['county'] as String? ?? '';

      if (street.isNotEmpty && _addressController.text.isEmpty) {
        _addressController.text = street;
      }
      if (city.isNotEmpty && _cityController.text.isEmpty) {
        _cityController.text = city;
      }
      if (province.isNotEmpty && _provinceController.text.isEmpty) {
        _provinceController.text = province;
      }
    } on Exception catch (_) {
      // Geocoding unavailable — user fills manually
    }
  }

  Future<void> _getLocationAndGeocode() async {
    if (_capture == null) return;
    setState(() => _gettingLocation = true);
    try {
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 10),
        ),
      );
      if (!mounted) return;
      setState(() {
        _gettingLocation = false;
        _capture = PhotoCapture(
          imagePath: _capture!.imagePath,
          timestamp: _capture!.timestamp,
          orientation: _capture!.orientation,
          latitude: position.latitude,
          longitude: position.longitude,
          accuracyMeters: position.accuracy,
        );
      });
      await _reverseGeocode(position.latitude, position.longitude);
    } on Exception catch (_) {
      if (mounted) setState(() => _gettingLocation = false);
    }
  }

  Future<void> _openCamera() async {
    final capture = await context.push<PhotoCapture>(AppRoutes.camera);
    if (capture == null || !mounted) return;
    setState(() => _capture = capture);
    if (capture.latitude != null && capture.longitude != null) {
      await _reverseGeocode(capture.latitude!, capture.longitude!);
    }
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
    } on Exception catch (_) {
      // GPS unavailable — user sees warning in form
    }

    if (!mounted) return;
    final newCapture = PhotoCapture(
      imagePath: xFile.path,
      timestamp: DateTime.now(),
      orientation: DeviceOrientation.portraitUp,
      latitude: position?.latitude,
      longitude: position?.longitude,
      accuracyMeters: position?.accuracy,
    );
    setState(() {
      _gettingLocation = false;
      _capture = newCapture;
    });
    if (position != null) {
      await _reverseGeocode(position.latitude, position.longitude);
    }
  }

  Future<void> _submit() async {
    if (_capture == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Debes agregar una fotografía antes de enviar.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }
    if (!_formKey.currentState!.validate()) return;
    if (!_hasLocation) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Se requiere ubicación GPS para enviar el reporte.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }
    if (_submitting) return;

    setState(() => _submitting = true);
    try {
      await context.read<ReportsCubit>().create(
            imagePath: _capture!.imagePath,
            latitude: _capture!.latitude!,
            longitude: _capture!.longitude!,
            description: _descriptionController.text.trim().isEmpty
                ? null
                : _descriptionController.text.trim(),
            address: _addressController.text.trim().isEmpty
                ? null
                : _addressController.text.trim(),
            city: _cityController.text.trim().isEmpty
                ? null
                : _cityController.text.trim(),
            province: _provinceController.text.trim().isEmpty
                ? null
                : _provinceController.text.trim(),
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Reporte guardado. Se enviará cuando haya conexión.'),
          backgroundColor: AppColors.secondary,
        ),
      );
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al guardar: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<ReportsCubit, ReportsState>(
      listener: (context, state) {
        if (state is ReportsError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.message),
              backgroundColor: AppColors.error,
            ),
          );
        }
      },
      child: Scaffold(
        appBar: AppBar(title: const Text('Nuevo reporte')),
        body: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // ── Imagen ──────────────────────────────────────────────────
              _SectionCard(
                title: 'Fotografía',
                required: true,
                child: _capture != null
                    ? _PhotoPreviewWithChange(
                        imagePath: _capture!.imagePath,
                        onCamera: _gettingLocation ? null : _openCamera,
                        onGallery: _gettingLocation ? null : _openGallery,
                      )
                    : _PhotoPicker(
                        onCamera: _gettingLocation ? null : _openCamera,
                        onGallery: _gettingLocation ? null : _openGallery,
                        isLoading: _gettingLocation,
                      ),
              ),
              const SizedBox(height: 12),

              // ── Ubicación ───────────────────────────────────────────────
              _SectionCard(
                title: 'Ubicación',
                required: true,
                child: _hasLocation
                    ? _LocationContent(capture: _capture!)
                    : _NoLocationWarning(
                        showButton: _capture != null,
                        isLoading: _gettingLocation,
                        onGetLocation: _getLocationAndGeocode,
                      ),
              ),
              const SizedBox(height: 12),

              // ── Dirección ───────────────────────────────────────────────
              _SectionCard(
                title: 'Dirección',
                subtitle: 'Se autocompletará cuando haya conexión (opcional).',
                child: Column(
                  children: [
                    TextFormField(
                      controller: _addressController,
                      decoration: const InputDecoration(
                        labelText: 'Dirección',
                        hintText: 'Ej. Av. Principal 123',
                        border: OutlineInputBorder(),
                      ),
                      maxLength: 500,
                      textCapitalization: TextCapitalization.words,
                      validator: (v) {
                        if ((v?.length ?? 0) > 500) {
                          return 'Máximo 500 caracteres';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _cityController,
                            decoration: const InputDecoration(
                              labelText: 'Ciudad',
                              hintText: 'Ciudad',
                              border: OutlineInputBorder(),
                            ),
                            maxLength: 100,
                            textCapitalization: TextCapitalization.words,
                            validator: (v) {
                              if ((v?.length ?? 0) > 100) {
                                return 'Máximo 100 caracteres';
                              }
                              return null;
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _provinceController,
                            decoration: const InputDecoration(
                              labelText: 'Provincia',
                              hintText: 'Provincia',
                              border: OutlineInputBorder(),
                            ),
                            maxLength: 100,
                            textCapitalization: TextCapitalization.words,
                            validator: (v) {
                              if ((v?.length ?? 0) > 100) {
                                return 'Máximo 100 caracteres';
                              }
                              return null;
                            },
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // ── Descripción ─────────────────────────────────────────────
              _SectionCard(
                title: 'Descripción',
                child: _DescriptionField(controller: _descriptionController),
              ),
              const SizedBox(height: 24),

              // ── Botones ─────────────────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed:
                          _submitting ? null : () => Navigator.of(context).pop(),
                      child: const Text('Cancelar'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: FilledButton.icon(
                      onPressed: _submitting ? null : _submit,
                      icon: _submitting
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: AppColors.onPrimary,
                              ),
                            )
                          : const Icon(Icons.send_rounded),
                      label: Text(_submitting ? 'Guardando…' : 'Enviar reporte'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Sin conexión, el reporte se guardará localmente\n'
                'y se enviará al reconectar automáticamente.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Widgets ────────────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.child,
    this.subtitle,
    this.required = false,
  });

  final String title;
  final String? subtitle;
  final Widget child;
  final bool required;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.outlineVariant),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                title,
                style: Theme.of(context)
                    .textTheme
                    .titleSmall
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              if (required)
                const Text(
                  ' *',
                  style: TextStyle(
                    color: AppColors.error,
                    fontWeight: FontWeight.bold,
                  ),
                ),
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 2),
            Text(
              subtitle!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _PhotoPicker extends StatelessWidget {
  const _PhotoPicker({
    required this.onCamera,
    required this.onGallery,
    required this.isLoading,
  });

  final VoidCallback? onCamera;
  final VoidCallback? onGallery;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const SizedBox(
        height: 80,
        child: Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(color: AppColors.primary),
              SizedBox(width: 12),
              Text('Obteniendo ubicación…'),
            ],
          ),
        ),
      );
    }
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: onCamera,
            icon: const Icon(Icons.camera_alt_rounded),
            label: const Text('Cámara'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: onGallery,
            icon: const Icon(Icons.photo_library_rounded),
            label: const Text('Galería'),
          ),
        ),
      ],
    );
  }
}

class _PhotoPreviewWithChange extends StatelessWidget {
  const _PhotoPreviewWithChange({
    required this.imagePath,
    required this.onCamera,
    required this.onGallery,
  });

  final String imagePath;
  final VoidCallback? onCamera;
  final VoidCallback? onGallery;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.file(
            File(imagePath),
            height: 200,
            width: double.infinity,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              height: 200,
              color: AppColors.surfaceVariant,
              child: const Icon(Icons.image_not_supported_outlined, size: 48),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextButton.icon(
                onPressed: onCamera,
                icon: const Icon(Icons.camera_alt_rounded, size: 18),
                label: const Text('Retomar'),
              ),
            ),
            Expanded(
              child: TextButton.icon(
                onPressed: onGallery,
                icon: const Icon(Icons.photo_library_rounded, size: 18),
                label: const Text('Cambiar'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _LocationContent extends StatelessWidget {
  const _LocationContent({required this.capture});

  final PhotoCapture capture;

  @override
  Widget build(BuildContext context) {
    final lat = capture.latitude!;
    final lng = capture.longitude!;
    final latStr = lat.toStringAsFixed(6);
    final lngStr = lng.toStringAsFixed(6);
    final accuracy = capture.accuracyMeters != null
        ? ' ± ${capture.accuracyMeters!.toStringAsFixed(0)} m'
        : '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.location_on_rounded,
                size: 20, color: AppColors.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('$latStr, $lngStr',
                      style: Theme.of(context).textTheme.bodyMedium),
                  if (accuracy.isNotEmpty)
                    Text(
                      'Precisión$accuracy',
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color:
                                Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                ],
              ),
            ),
            const Icon(Icons.check_circle_rounded,
                size: 18, color: AppColors.statusResolved),
          ],
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: SizedBox(
            height: 200,
            child: FlutterMap(
              options: MapOptions(
                initialCenter: LatLng(lat, lng),
                initialZoom: 16,
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.none,
                ),
              ),
              children: [
                TileLayer(
                  urlTemplate:
                      'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.sirccd.mobile',
                  errorTileCallback: (tile, error, stackTrace) {},
                ),
                MarkerLayer(
                  markers: [
                    Marker(
                      point: LatLng(lat, lng),
                      child: const Icon(
                        Icons.location_pin,
                        color: AppColors.error,
                        size: 40,
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

class _NoLocationWarning extends StatelessWidget {
  const _NoLocationWarning({
    required this.showButton,
    required this.isLoading,
    required this.onGetLocation,
  });

  final bool showButton;
  final bool isLoading;
  final VoidCallback onGetLocation;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.location_off_rounded,
                size: 20, color: AppColors.warning),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Sin ubicación GPS. Activa el GPS y obtén la ubicación.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.warning,
                    ),
              ),
            ),
          ],
        ),
        if (showButton) ...[
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: isLoading ? null : onGetLocation,
              icon: isLoading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.my_location_rounded, size: 18),
              label: Text(isLoading ? 'Obteniendo ubicación…' : 'Obtener ubicación'),
            ),
          ),
        ],
      ],
    );
  }
}

class _DescriptionField extends StatefulWidget {
  const _DescriptionField({required this.controller});

  final TextEditingController controller;

  @override
  State<_DescriptionField> createState() => _DescriptionFieldState();
}

class _DescriptionFieldState extends State<_DescriptionField> {
  @override
  void initState() {
    super.initState();
    widget.controller.addListener(() => setState(() {}));
  }

  @override
  Widget build(BuildContext context) {
    final length = widget.controller.text.length;
    return Stack(
      children: [
        TextFormField(
          controller: widget.controller,
          decoration: const InputDecoration(
            hintText: 'Describe el daño vial que encontraste (opcional)',
            border: OutlineInputBorder(),
            alignLabelWithHint: true,
          ),
          maxLines: 4,
          maxLength: 2000,
          buildCounter: (_, {required currentLength, required isFocused, maxLength}) =>
              const SizedBox.shrink(),
          textCapitalization: TextCapitalization.sentences,
          validator: (v) {
            if ((v?.length ?? 0) > 2000) return 'Máximo 2000 caracteres';
            return null;
          },
        ),
        Positioned(
          bottom: 10,
          right: 12,
          child: Text(
            '$length/2000',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: length > 1900
                      ? AppColors.error
                      : Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
        ),
      ],
    );
  }
}
