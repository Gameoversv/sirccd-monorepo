import 'package:dio/dio.dart';
import 'package:sirccd_mobile/features/profile/data/models/user_profile_model.dart';

abstract interface class ProfileRemoteDataSource {
  Future<UserProfileModel> getCurrentUser(String token);
}

final class ProfileRemoteDataSourceImpl implements ProfileRemoteDataSource {
  const ProfileRemoteDataSourceImpl(this._dio);

  final Dio _dio;

  @override
  Future<UserProfileModel> getCurrentUser(String token) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/auth/me',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return UserProfileModel.fromJson(response.data!);
  }
}
