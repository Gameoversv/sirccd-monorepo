import 'package:dio/dio.dart';
import 'package:sirccd_mobile/features/auth/data/models/login_response.dart';

abstract interface class AuthRemoteDataSource {
  Future<LoginResponse> login(String email, String password);
}

final class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  const AuthRemoteDataSourceImpl(this._dio);

  final Dio _dio;

  @override
  Future<LoginResponse> login(String email, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'email': email, 'password': password},
    );
    return LoginResponse.fromJson(response.data!);
  }
}
