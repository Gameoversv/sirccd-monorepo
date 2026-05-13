import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class PhotoPreview extends StatelessWidget {
  const PhotoPreview({
    super.key,
    required this.capture,
    required this.onRetake,
    required this.onAccept,
  });

  final PhotoCapture capture;
  final VoidCallback onRetake;
  final ValueChanged<PhotoCapture> onAccept;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        Image.file(File(capture.imagePath), fit: BoxFit.cover),
        _MetadataBar(capture: capture),
        _ActionRow(
          onRetake: onRetake,
          onAccept: () => onAccept(capture),
        ),
      ],
    );
  }
}

class _MetadataBar extends StatelessWidget {
  const _MetadataBar({required this.capture});

  final PhotoCapture capture;

  @override
  Widget build(BuildContext context) {
    final dateStr = _formatTimestamp(capture.timestamp);
    final orientLabel = _orientationLabel(capture.orientation);

    return Positioned(
      top: MediaQuery.of(context).padding.top + 12,
      left: 12,
      right: 12,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.65),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            _MetaRow(
              icon: Icons.access_time_rounded,
              text: dateStr,
            ),
            if (capture.hasLocation) ...[
              const SizedBox(height: 4),
              _MetaRow(
                icon: Icons.location_on_rounded,
                text: _locationText(capture),
              ),
            ] else ...[
              const SizedBox(height: 4),
              _MetaRow(
                icon: Icons.location_off_rounded,
                text: 'Ubicación no disponible',
                muted: true,
              ),
            ],
            const SizedBox(height: 4),
            _MetaRow(
              icon: Icons.screen_rotation_rounded,
              text: orientLabel,
            ),
          ],
        ),
      ),
    );
  }

  static const _months = [
    '', 'ene', 'feb', 'mar', 'abr', 'may', 'jun',
    'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
  ];

  String _formatTimestamp(DateTime dt) {
    final d = dt.day.toString().padLeft(2, '0');
    final m = _months[dt.month];
    final y = dt.year;
    final h = dt.hour.toString().padLeft(2, '0');
    final min = dt.minute.toString().padLeft(2, '0');
    return '$d $m $y, $h:$min';
  }

  String _locationText(PhotoCapture c) {
    final lat = c.latitude!.toStringAsFixed(5);
    final lng = c.longitude!.toStringAsFixed(5);
    final acc = c.accuracyMeters != null
        ? ' (±${c.accuracyMeters!.toStringAsFixed(0)}m)'
        : '';
    return '$lat, $lng$acc';
  }

  String _orientationLabel(DeviceOrientation o) => switch (o) {
        DeviceOrientation.portraitUp => 'Retrato',
        DeviceOrientation.portraitDown => 'Retrato invertido',
        DeviceOrientation.landscapeLeft => 'Paisaje izquierda',
        DeviceOrientation.landscapeRight => 'Paisaje derecha',
      };
}

class _MetaRow extends StatelessWidget {
  const _MetaRow({
    required this.icon,
    required this.text,
    this.muted = false,
  });

  final IconData icon;
  final String text;
  final bool muted;

  @override
  Widget build(BuildContext context) {
    final color = muted
        ? Colors.white.withValues(alpha: 0.5)
        : Colors.white.withValues(alpha: 0.9);
    return Row(
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            style: TextStyle(color: color, fontSize: 12),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

class _ActionRow extends StatelessWidget {
  const _ActionRow({required this.onRetake, required this.onAccept});

  final VoidCallback onRetake;
  final VoidCallback onAccept;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: 0,
      left: 0,
      right: 0,
      child: Container(
        padding: EdgeInsets.fromLTRB(
          24,
          16,
          24,
          MediaQuery.of(context).padding.bottom + 24,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.bottomCenter,
            end: Alignment.topCenter,
            colors: [
              Colors.black.withValues(alpha: 0.8),
              Colors.transparent,
            ],
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: onRetake,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retomar'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white54),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: FilledButton.icon(
                onPressed: onAccept,
                icon: const Icon(Icons.check_rounded),
                label: const Text('Usar foto'),
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
