import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:sirccd_mobile/core/services/connectivity_service.dart';
import 'package:sirccd_mobile/core/services/database_service.dart';
import 'package:sirccd_mobile/core/services/permission_service.dart';
import 'package:sirccd_mobile/core/services/session_service.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:sirccd_mobile/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:sirccd_mobile/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/get_stored_token_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/login_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/logout_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/register_usecase.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_cubit.dart';
import 'package:sirccd_mobile/features/camera/data/datasources/camera_datasource.dart';
import 'package:sirccd_mobile/features/camera/data/repositories/camera_repository_impl.dart';
import 'package:sirccd_mobile/features/camera/domain/repositories/camera_repository.dart';
import 'package:sirccd_mobile/features/camera/domain/usecases/capture_photo_usecase.dart';
import 'package:sirccd_mobile/features/camera/presentation/cubit/camera_cubit.dart';
import 'package:sirccd_mobile/features/profile/data/datasources/profile_remote_datasource.dart';
import 'package:sirccd_mobile/features/profile/data/repositories/profile_repository_impl.dart';
import 'package:sirccd_mobile/features/profile/domain/repositories/profile_repository.dart';
import 'package:sirccd_mobile/features/profile/domain/usecases/get_current_profile_usecase.dart';
import 'package:sirccd_mobile/features/profile/presentation/cubit/profile_cubit.dart';
import 'package:sirccd_mobile/features/reports/data/datasources/report_local_datasource.dart';
import 'package:sirccd_mobile/features/reports/data/datasources/report_remote_datasource.dart';
import 'package:sirccd_mobile/features/reports/data/repositories/report_repository_impl.dart';
import 'package:sirccd_mobile/features/reports/domain/repositories/report_repository.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/create_pending_report_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/get_all_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/get_report_detail_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/get_user_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/delete_all_local_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/domain/usecases/sync_pending_reports_usecase.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_detail_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/report_history_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_cubit.dart';

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
    // ── Core ────────────────────────────────────────────────────────────────
    ..registerSingleton<AuthLocalDataSource>(AuthLocalDataSourceImpl(storage))
    ..registerSingleton<AuthRemoteDataSource>(AuthRemoteDataSourceImpl(dio))
    ..registerSingleton<AuthRepository>(
      AuthRepositoryImpl(di<AuthRemoteDataSource>(), di<AuthLocalDataSource>()),
    )
    ..registerSingleton(LoginUseCase(di<AuthRepository>()))
    ..registerSingleton(RegisterUseCase(di<AuthRepository>()))
    ..registerSingleton(LogoutUseCase(di<AuthRepository>()))
    ..registerSingleton(GetStoredTokenUseCase(di<AuthRepository>()))
    ..registerSingleton(PermissionService())
    ..registerSingleton<DatabaseService>(DatabaseServiceImpl())
    ..registerSingleton<ConnectivityService>(ConnectivityServiceImpl())
    ..registerSingleton(SessionService())
    ..registerFactory(
      () => AuthCubit(
        di<LoginUseCase>(),
        di<RegisterUseCase>(),
        di<LogoutUseCase>(),
        di<GetStoredTokenUseCase>(),
        di<SessionService>(),
      ),
    )
    // Profile
    ..registerSingleton<ProfileRemoteDataSource>(
      ProfileRemoteDataSourceImpl(dio),
    )
    ..registerSingleton<ProfileRepository>(
      ProfileRepositoryImpl(
        di<ProfileRemoteDataSource>(),
        di<AuthLocalDataSource>(),
        di<SessionService>(),
      ),
    )
    ..registerSingleton(GetCurrentProfileUseCase(di<ProfileRepository>()))
    ..registerFactory(() => ProfileCubit(di<GetCurrentProfileUseCase>()))
    // ── Camera ───────────────────────────────────────────────────────────────
    ..registerSingleton<CameraDatasource>(CameraDatasourceImpl())
    ..registerSingleton<CameraRepository>(
      CameraRepositoryImpl(di<CameraDatasource>()),
    )
    ..registerSingleton(CapturePhotoUseCase(di<CameraRepository>()))
    ..registerFactory(() => CameraCubit(di<CapturePhotoUseCase>()))
    // ── Reports ──────────────────────────────────────────────────────────────
    ..registerSingleton<ReportLocalDataSource>(
      ReportLocalDataSourceImpl(di<DatabaseService>()),
    )
    ..registerSingleton<ReportRemoteDataSource>(ReportRemoteDataSourceImpl(dio))
    ..registerSingleton<ReportRepository>(
      ReportRepositoryImpl(
        di<ReportLocalDataSource>(),
        di<ReportRemoteDataSource>(),
        di<AuthLocalDataSource>(),
        di<ConnectivityService>(),
        di<SessionService>(),
      ),
    )
    ..registerSingleton(CreatePendingReportUseCase(di<ReportRepository>()))
    ..registerSingleton(GetAllReportsUseCase(di<ReportRepository>()))
    ..registerSingleton(SyncPendingReportsUseCase(di<ReportRepository>()))
    ..registerSingleton(GetUserReportsUseCase(di<ReportRepository>()))
    ..registerSingleton(GetReportDetailUseCase(di<ReportRepository>()))
    ..registerSingleton(DeleteAllLocalReportsUseCase(di<ReportRepository>()))
    ..registerFactory(
      () => ReportsCubit(
        di<CreatePendingReportUseCase>(),
        di<GetAllReportsUseCase>(),
        di<SyncPendingReportsUseCase>(),
        di<ConnectivityService>(),
        di<DeleteAllLocalReportsUseCase>(),
      ),
    )
    ..registerFactory(() => ReportHistoryCubit(di<GetUserReportsUseCase>()))
    ..registerFactory(() => ReportDetailCubit(di<GetReportDetailUseCase>()));
}
