import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/reports/data/models/user_report_model.dart';

void main() {
  group('UserReportModel', () {
    test('rewrites loopback asset URLs to the configured API host', () {
      final report = UserReportModel.fromJson({
        'id': 12,
        'latitude': 37.4219983,
        'longitude': -122.084,
        'address': 'Amphitheatre Parkway',
        'city': 'Mountain View',
        'province': 'California',
        'status': 'pending',
        'damage_type': 'bache',
        'severity': 'baja',
        'confidence': 0.0,
        'image_url': 'http://localhost:9000/sirccd-images/reports/photo.jpg',
        'annotated_image_url':
            'http://127.0.0.1:9000/sirccd-images/reports/annotated.jpg',
        'description': null,
        'rejection_reason': null,
        'created_at': '2026-07-07T23:59:00Z',
        'updated_at': '2026-07-07T23:59:00Z',
        'reviewed_at': null,
      });

      expect(
        report.imageUrl,
        'http://10.0.2.2:9000/sirccd-images/reports/photo.jpg',
      );
      expect(
        report.annotatedImageUrl,
        'http://10.0.2.2:9000/sirccd-images/reports/annotated.jpg',
      );
    });

    test('leaves non-loopback asset URLs unchanged', () {
      final report = UserReportModel.fromJson({
        'id': 13,
        'latitude': 18.4861,
        'longitude': -69.9312,
        'status': 'approved',
        'image_url': 'https://cdn.example.com/reports/photo.jpg',
        'annotated_image_url': null,
        'created_at': '2026-07-07T23:59:00Z',
        'updated_at': '2026-07-07T23:59:00Z',
      });

      expect(report.imageUrl, 'https://cdn.example.com/reports/photo.jpg');
      expect(report.annotatedImageUrl, isNull);
    });

    test('extracts ML metadata from detections_json', () {
      final report = UserReportModel.fromJson({
        'id': 14,
        'latitude': 18.4861,
        'longitude': -69.9312,
        'status': 'approved',
        'damage_type': 'grieta',
        'severity': 'media',
        'confidence': 0.91,
        'image_url': '/storage/images/reports/photo.jpg',
        'annotated_image_url': null,
        'detections_json': jsonEncode({
          'annotated_image_url': '/storage/images/annotated/photo.jpg',
          'model_version': 'rd-roaddataset/5',
          'num_detections': 2,
          'model_precision': 0.77,
          'model_recall': '0.66',
          'model_map50': 83.4,
          'bounding_boxes': [
            {'class': 'grieta'},
            {'class': 'grieta'},
          ],
        }),
        'created_at': '2026-07-07T23:59:00Z',
        'updated_at': '2026-07-07T23:59:00Z',
      });

      expect(
        report.imageUrl,
        'http://10.0.2.2:8000/storage/images/reports/photo.jpg',
      );
      expect(
        report.annotatedImageUrl,
        'http://10.0.2.2:8000/storage/images/annotated/photo.jpg',
      );
      expect(report.modelVersion, 'rd-roaddataset/5');
      expect(report.detectionCount, 2);
      expect(report.modelPrecision, 0.77);
      expect(report.modelRecall, 0.66);
      expect(report.modelMap50, 83.4);
    });

    test('reads the severity breakdown out of detections_json', () {
      // Arrange: foto a 2x — el backend guarda el desglose dentro del JSON
      final report = UserReportModel.fromJson({
        'id': 5,
        'latitude': 18.48,
        'longitude': -69.93,
        'status': 'approved',
        'image_url': '/api/v1/reportes/5/image',
        'created_at': '2026-07-16T21:07:00Z',
        'updated_at': '2026-07-16T21:07:00Z',
        'detections_json': jsonEncode({
          'damage_ratio_raw': 0.1875,
          'damage_ratio_normalized': 0.046875,
          'focal_scale_factor': 0.5,
          'area_scale_factor': 0.25,
          'weighted_detections': 0.4,
        }),
      });

      // Assert
      expect(report.damageRatioRaw, 0.1875);
      expect(report.damageRatioNormalized, 0.046875);
      expect(report.focalScaleFactor, 0.5);
      expect(report.areaScaleFactor, 0.25);
      expect(report.weightedDetections, 0.4);
    });

    test('prefers top-level breakdown fields over detections_json', () {
      // El detalle los expone arriba; el listado solo trae detections_json.
      final report = UserReportModel.fromJson({
        'id': 5,
        'latitude': 18.48,
        'longitude': -69.93,
        'status': 'approved',
        'image_url': '/api/v1/reportes/5/image',
        'created_at': '2026-07-16T21:07:00Z',
        'updated_at': '2026-07-16T21:07:00Z',
        'damage_ratio_normalized': 0.5,
        'detections_json': jsonEncode({'damage_ratio_normalized': 0.1}),
      });

      expect(report.damageRatioNormalized, 0.5);
    });

    test('leaves the breakdown null for reports processed before it existed', () {
      final report = UserReportModel.fromJson({
        'id': 4,
        'latitude': 18.48,
        'longitude': -69.93,
        'status': 'approved',
        'image_url': '/api/v1/reportes/4/image',
        'created_at': '2026-07-16T20:38:00Z',
        'updated_at': '2026-07-16T20:38:00Z',
        'detections_json': jsonEncode({'severity': 'baja', 'confidence': 0.87}),
      });

      expect(report.damageRatioRaw, isNull);
      expect(report.focalScaleFactor, isNull);
    });
  });
}
