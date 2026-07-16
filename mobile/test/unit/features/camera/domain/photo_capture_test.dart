import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';

PhotoCapture _capture({double? zoomLevel}) => PhotoCapture(
  imagePath: '/tmp/photo.jpg',
  timestamp: DateTime(2026, 7, 8),
  orientation: DeviceOrientation.portraitUp,
  zoomLevel: zoomLevel,
);

void main() {
  group('PhotoCapture', () {
    test('has no focal scale factor when zoom is unknown', () {
      expect(_capture().focalScaleFactor, isNull);
    });

    test('converts camera zoom into focal scale factor', () {
      expect(_capture(zoomLevel: 1).focalScaleFactor, 1);
      expect(_capture(zoomLevel: 2).focalScaleFactor, 0.5);
    });

    test('clamps focal scale factor to backend supported range', () {
      expect(_capture(zoomLevel: 10).focalScaleFactor, 0.25);
      expect(_capture(zoomLevel: 0.25).focalScaleFactor, 2.0);
    });
  });
}
