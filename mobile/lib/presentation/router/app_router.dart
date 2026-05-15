import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_cubit.dart';
import 'package:sirccd_mobile/features/reports/presentation/cubit/reports_cubit.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_state.dart';
import 'package:sirccd_mobile/features/auth/presentation/pages/login_page.dart';
import 'package:sirccd_mobile/features/auth/presentation/pages/splash_page.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/features/camera/presentation/pages/camera_page.dart';
import 'package:sirccd_mobile/features/permissions/presentation/pages/permission_rationale_page.dart';
import 'package:sirccd_mobile/features/profile/presentation/pages/profile_page.dart';
import 'package:sirccd_mobile/features/reports/presentation/pages/new_report_page.dart';
import 'package:sirccd_mobile/features/reports/presentation/pages/reports_page.dart';
import 'package:sirccd_mobile/presentation/widgets/app_shell.dart';

abstract final class AppRoutes {
  static const splash = '/';
  static const login = '/login';
  static const permissions = '/permissions';
  static const home = '/home';
  static const reports = '/reports';
  static const newReport = '/reports/new';
  static const profile = '/profile';
  static const camera = '/camera';
}

class AppRouter {
  AppRouter(AuthCubit authCubit) : _authCubit = authCubit {
    router = GoRouter(
      initialLocation: AppRoutes.splash,
      refreshListenable: _GoRouterRefreshStream(authCubit.stream),
      redirect: _redirect,
      routes: [
        GoRoute(
          path: AppRoutes.splash,
          builder: (_, __) => const SplashPage(),
        ),
        GoRoute(
          path: AppRoutes.login,
          builder: (_, __) => const LoginPage(),
        ),
        GoRoute(
          path: AppRoutes.permissions,
          builder: (_, __) => const PermissionRationalePage(),
        ),
        GoRoute(
          path: AppRoutes.camera,
          builder: (_, __) => const CameraPage(),
        ),
        GoRoute(
          path: AppRoutes.newReport,
          builder: (context, state) => BlocProvider(
            create: (_) => di<ReportsCubit>()..init(),
            child: NewReportPage(
              capture: state.extra as PhotoCapture?,
            ),
          ),
        ),
        ShellRoute(
          builder: (context, state, child) => AppShell(child: child),
          routes: [
            GoRoute(
              path: AppRoutes.home,
              builder: (_, __) => const ReportsPage(),
            ),
            GoRoute(
              path: AppRoutes.reports,
              builder: (_, __) => const ReportsPage(),
            ),
            GoRoute(
              path: AppRoutes.profile,
              builder: (_, __) => const ProfilePage(),
            ),
          ],
        ),
      ],
    );
  }

  final AuthCubit _authCubit;
  late final GoRouter router;

  FutureOr<String?> _redirect(BuildContext context, GoRouterState state) {
    final authState = _authCubit.state;
    final loc = state.matchedLocation;

    if (loc == AppRoutes.splash) {
      if (authState is AuthAuthenticated) return AppRoutes.permissions;
      if (authState is AuthUnauthenticated || authState is AuthError) {
        return AppRoutes.login;
      }
      return null;
    }

    final isAuth = authState is AuthAuthenticated;

    if (!isAuth && loc != AppRoutes.login) return AppRoutes.login;
    if (isAuth && loc == AppRoutes.login) return AppRoutes.permissions;

    return null;
  }
}

class _GoRouterRefreshStream extends ChangeNotifier {
  _GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _sub = stream.asBroadcastStream().listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
