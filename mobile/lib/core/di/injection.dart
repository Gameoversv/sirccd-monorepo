import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:sirccd_mobile/core/services/permission_service.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:sirccd_mobile/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/get_stored_token_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/login_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/logout_usecase.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_cubit.dart';
import 'package:sirccd_mobile/features/camera/data/datasources/camera_datasource.dart';
import 'package:sirccd_mobile/features/camera/data/repositories/camera_repository_impl.dart';
import 'package:sirccd_mobile/features/camera/domain/repositories/camera_repository.dart';
import 'package:sirccd_mobile/features/camera/domain/usecases/capture_photo_usecase.dart';
import 'package:sirccd_mobile/features/camera/presentation/cubit/camera_cubit.dart';

final di = GetIt.instance;

Future<void> initDependencies() async {
  const storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  final dio = Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000/api/v1',
      ),
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ),
  );

  di
    ..registerSingleton<AuthLocalDataSource>(AuthLocalDataSourceImpl(storage))
    ..registerSingleton<AuthRemoteDataSource>(AuthRemoteDataSourceImpl(dio))
    ..registerSingleton<AuthRepository>(
      AuthRepositoryImpl(
        di<AuthRemoteDataSource>(),
        di<AuthLocalDataSource>(),
      ),
    )
    ..registerSingleton(LoginUseCase(di<AuthRepository>()))
    ..registerSingleton(LogoutUseCase(di<AuthRepository>()))
    ..registerSingleton(GetStoredTokenUseCase(di<AuthRepository>()))
    ..registerSingleton(PermissionService())
    ..registerFactory(
      () => AuthCubit(
        di<LoginUseCase>(),
        di<LogoutUseCase>(),
        di<GetStoredTokenUseCase>(),
      ),
    )
    // Camera
    ..registerSingleton<CameraDatasource>(CameraDatasourceImpl())
    ..registerSingleton<CameraRepository>(
      CameraRepositoryImpl(di<CameraDatasource>()),
    )
    ..registerSingleton(CapturePhotoUseCase(di<CameraRepository>()))
    ..registerFactory(() => CameraCubit(di<CapturePhotoUseCase>()));
}
