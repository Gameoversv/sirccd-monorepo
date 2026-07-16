import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/reports/data/datasources/report_remote_datasource.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';

class _RecordingAdapter implements HttpClientAdapter {
  RequestOptions? lastOptions;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastOptions = options;
    await requestStream?.drain<void>();
    return ResponseBody.fromString(
      jsonEncode({'id': 42}),
      201,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  group('ReportRemoteDataSourceImpl', () {
    test('submitReport uses backend multipart field names', () async {
      final tempDir = await Directory.systemTemp.createTemp(
        'sirccd_mobile_test_',
      );
      addTearDown(() async {
        if (await tempDir.exists()) await tempDir.delete(recursive: true);
      });

      final image = File('${tempDir.path}${Platform.pathSeparator}report.jpg');
      await image.writeAsBytes([0, 1, 2, 3]);

      final adapter = _RecordingAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'http://test.local/api/v1'))
        ..httpClientAdapter = adapter;
      final datasource = ReportRemoteDataSourceImpl(dio);

      final id = await datasource.submitReport(
        PendingReport(
          localId: 'local-1',
          imagePath: image.path,
          latitude: 18.4861,
          longitude: -69.9312,
          description: 'Bache frente al parque',
          address: 'Av. Principal',
          city: 'Santo Domingo',
          province: 'Distrito Nacional',
          focalScaleFactor: 0.5,
          syncStatus: SyncStatus.pending,
          createdAt: DateTime(2026, 7, 7),
        ),
        'test-token',
      );

      expect(id, 42);

      final options = adapter.lastOptions;
      expect(options, isNotNull);
      expect(options!.path, '/reportes');
      expect(options.method, 'POST');
      expect(options.headers['Authorization'], 'Bearer test-token');

      final formData = options.data as FormData;
      final fields = {
        for (final field in formData.fields) field.key: field.value,
      };

      expect(fields.containsKey('latitude'), isTrue);
      expect(fields.containsKey('longitude'), isTrue);
      expect(fields.containsKey('lat'), isFalse);
      expect(fields.containsKey('lng'), isFalse);
      expect(fields['description'], 'Bache frente al parque');
      expect(fields['address'], 'Av. Principal');
      expect(fields['city'], 'Santo Domingo');
      expect(fields['province'], 'Distrito Nacional');
      expect(fields['focal_scale_factor'], '0.5');
      expect(formData.files.single.key, 'image');
    });
  });
}
