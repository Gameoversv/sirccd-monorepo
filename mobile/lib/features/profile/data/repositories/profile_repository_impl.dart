import 'package:dio/dio.dart';
import 'package:sirccd_mobile/core/errors/failures.dart';
import 'package:sirccd_mobile/core/services/session_service.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:sirccd_mobile/features/profile/data/datasources/profile_remote_datasource.dart';
import 'package:sirccd_mobile/features/profile/domain/entities/user_profile.dart';
import 'package:sirccd_mobile/features/profile/domain/repositories/profile_repository.dart';

final class ProfileRepositoryImpl implements ProfileRepository {
  const ProfileRepositoryImpl(this._remote, this._auth, this._session);

  final ProfileRemoteDataSource _remote;
  final AuthLocalDataSource _auth;
  final SessionService _session;

  @override
  Future<UserProfile> getCurrentUser() async {
    final token = await _auth.getToken();
    if (token == null) {
      _session.notifyExpired();
      throw const AuthFailure('Sesion expirada.');
    }

    try {
      return _remote.getCurrentUser(token);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403) {
        _session.notifyExpired();
        throw const AuthFailure('Sesion expirada.');
      }
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.connectionError) {
        throw const NetworkFailure();
      }
      throw ServerFailure(e.message ?? 'Error del servidor.');
    } catch (e) {
      throw UnknownFailure('$e');
    }
  }
}
