import 'package:dio/dio.dart';
import 'package:sirccd_mobile/core/errors/failures.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:sirccd_mobile/features/auth/domain/entities/auth_token.dart';
import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';

final class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl(this._remote, this._local);

  final AuthRemoteDataSource _remote;
  final AuthLocalDataSource _local;

  @override
  Future<AuthToken> login(String email, String password) async {
    try {
      final response = await _remote.login(email, password);
      await _local.saveToken(response.accessToken);
      return AuthToken(accessToken: response.accessToken);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403) throw const AuthFailure();
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.connectionError) {
        throw const NetworkFailure();
      }
      throw ServerFailure(e.message ?? 'Error del servidor.');
    } catch (e) {
      throw UnknownFailure('$e');
    }
  }

  @override
  Future<AuthToken> registerAndLogin({
    required String username,
    required String email,
    required String password,
    String? fullName,
  }) async {
    try {
      await _remote.register(
        username: username,
        email: email,
        password: password,
        fullName: fullName,
      );
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 400 || status == 409) {
        throw ServerFailure(_responseMessage(e, 'No se pudo crear la cuenta.'));
      }
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.connectionError) {
        throw const NetworkFailure();
      }
      throw ServerFailure(e.message ?? 'Error del servidor.');
    } catch (e) {
      throw UnknownFailure('$e');
    }

    return login(email, password);
  }

  @override
  Future<void> logout() => _local.deleteToken();

  @override
  Future<AuthToken?> getStoredToken() async {
    final token = await _local.getToken();
    if (token == null) return null;
    return AuthToken(accessToken: token);
  }

  String _responseMessage(DioException e, String fallback) {
    final data = e.response?.data;
    if (data is Map<String, dynamic> && data['detail'] is String) {
      return data['detail'] as String;
    }
    return e.message ?? fallback;
  }
}
