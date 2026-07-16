import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_remote_datasource.dart';

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
      jsonEncode({
        'message': 'Usuario registrado exitosamente',
        'user_id': 1,
        'username': 'roadwatch',
        'email': 'roadwatch@example.com',
      }),
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
  group('AuthRemoteDataSourceImpl', () {
    test('register sends the backend registration payload', () async {
      final adapter = _RecordingAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'http://test.local/api/v1'))
        ..httpClientAdapter = adapter;
      final datasource = AuthRemoteDataSourceImpl(dio);

      await datasource.register(
        username: 'roadwatch',
        email: 'roadwatch@example.com',
        password: 'Password123',
        fullName: ' Road Watch ',
      );

      final options = adapter.lastOptions;
      expect(options, isNotNull);
      expect(options!.path, '/auth/register');
      expect(options.method, 'POST');

      final data = options.data as Map<String, dynamic>;
      expect(data['username'], 'roadwatch');
      expect(data['email'], 'roadwatch@example.com');
      expect(data['password'], 'Password123');
      expect(data['full_name'], 'Road Watch');
    });

    test('register omits blank full name', () async {
      final adapter = _RecordingAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'http://test.local/api/v1'))
        ..httpClientAdapter = adapter;
      final datasource = AuthRemoteDataSourceImpl(dio);

      await datasource.register(
        username: 'roadwatch',
        email: 'roadwatch@example.com',
        password: 'Password123',
        fullName: '   ',
      );

      final data = adapter.lastOptions!.data as Map<String, dynamic>;
      expect(data.containsKey('full_name'), isFalse);
    });
  });
}
