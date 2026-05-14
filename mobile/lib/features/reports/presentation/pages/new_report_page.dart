import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_state.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class NewReportPage extends StatefulWidget {
  const NewReportPage({super.key, required this.capture});

  final PhotoCapture capture;

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

  @override
  void dispose() {
    _descriptionController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _provinceController.dispose();
    super.dispose();
  }

  bool get _hasLocation =>
      widget.capture.hasLocation &&
      widget.capture.latitude != null &&
      widget.capture.longitude != null &&
      widget.capture.latitude! >= -90 &&
      widget.capture.latitude! <= 90 &&
      widget.capture.longitude! >= -180 &&
      widget.capture.longitude! <= 180;

  Future<void> _submit() async {
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
            imagePath: widget.capture.imagePath,
            latitude: widget.capture.latitude!,
            longitude: widget.capture.longitude!,
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
                child: _PhotoPreview(imagePath: widget.capture.imagePath),
              ),
              const SizedBox(height: 12),

              // ── Ubicación ───────────────────────────────────────────────
              _SectionCard(
                title: 'Ubicación',
                required: true,
                child: _hasLocation
                    ? _LocationContent(capture: widget.capture)
                    : const _NoLocationWarning(),
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

class _PhotoPreview extends StatelessWidget {
  const _PhotoPreview({required this.imagePath});

  final String imagePath;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
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
  const _NoLocationWarning();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(Icons.location_off_rounded,
            size: 20, color: AppColors.warning),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            'Ubicación GPS no disponible. Activa el GPS e intenta de nuevo.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.warning,
                ),
          ),
        ),
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
