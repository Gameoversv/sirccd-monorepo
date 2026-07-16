import 'package:dio/dio.dart';
import 'package:sirccd_mobile/features/auth/data/models/login_response.dart';

abstract interface class AuthRemoteDataSource {
  Future<LoginResponse> login(String email, String password);
  Future<void> register({
    required String username,
    required String email,
    required String password,
    String? fullName,
  });
}

final class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  const AuthRemoteDataSourceImpl(this._dio);

  final Dio _dio;

  @override
  Future<LoginResponse> login(String email, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'username': email, 'password': password},
    );
    return LoginResponse.fromJson(response.data!);
  }

  @override
  Future<void> register({
    required String username,
    required String email,
    required String password,
    String? fullName,
  }) async {
    await _dio.post<Map<String, dynamic>>(
      '/auth/register',
      data: {
        'username': username,
        'email': email,
        'password': password,
        if (fullName != null && fullName.trim().isNotEmpty)
          'full_name': fullName.trim(),
      },
    );
  }
}
