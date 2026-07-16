import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/camera/presentation/pages/camera_page.dart';

void main() {
  group('previewCoverScale', () {
    // 16:9 es lo que reporta la mayoria de sensores como aspectRatio.
    const sensor16x9 = 1280 / 720;

    test('cubre una pantalla 1080x2400 en retrato sin sobreampliar', () {
      // CameraPreview renderiza 9:16 (0.5625) en retrato, quedando en
      // 1080x1920 dentro de la pantalla: hace falta 2400/1920 = 1.25.
      final scale = previewCoverScale(
        sensorAspectRatio: sensor16x9,
        screenSize: const Size(1080, 2400),
        isLandscape: false,
      );

      expect(scale, closeTo(1.25, 0.001));
    });

    test('cubre la misma pantalla en apaisado', () {
      final scale = previewCoverScale(
        sensorAspectRatio: sensor16x9,
        screenSize: const Size(2400, 1080),
        isLandscape: true,
      );

      expect(scale, closeTo(1.25, 0.001));
    });

    test('no escala cuando la vista previa ya calza con la pantalla', () {
      final scale = previewCoverScale(
        sensorAspectRatio: sensor16x9,
        screenSize: const Size(1080, 1920),
        isLandscape: false,
      );

      expect(scale, closeTo(1.0, 0.001));
    });

    test('nunca reduce: la escala siempre cubre la pantalla', () {
      const screens = [
        Size(1080, 2400),
        Size(1080, 1920),
        Size(1440, 3200),
        Size(720, 1280),
        Size(768, 1024),
      ];

      for (final screen in screens) {
        final scale = previewCoverScale(
          sensorAspectRatio: sensor16x9,
          screenSize: screen,
          isLandscape: false,
        );

        expect(
          scale,
          greaterThanOrEqualTo(1.0),
          reason: 'la vista previa dejaria franjas en $screen',
        );
      }
    });

    test('un sensor 4:3 en retrato sigue cubriendo sin ampliar de mas', () {
      // 4:3 -> retrato 0.75, pantalla 0.45 -> 0.75/0.45 = 1.667
      final scale = previewCoverScale(
        sensorAspectRatio: 4 / 3,
        screenSize: const Size(1080, 2400),
        isLandscape: false,
      );

      expect(scale, closeTo(1.667, 0.001));
    });

    test('devuelve 1 ante medidas invalidas en vez de dividir por cero', () {
      expect(
        previewCoverScale(
          sensorAspectRatio: 0,
          screenSize: const Size(1080, 2400),
          isLandscape: false,
        ),
        1,
      );
      expect(
        previewCoverScale(
          sensorAspectRatio: sensor16x9,
          screenSize: Size.zero,
          isLandscape: false,
        ),
        1,
      );
    });
  });
}
