import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sirccd_mobile/features/auth/presentation/pages/login_page.dart';
import 'package:sirccd_mobile/features/auth/presentation/pages/splash_page.dart';
import 'package:sirccd_mobile/features/profile/presentation/pages/profile_page.dart';
import 'package:sirccd_mobile/features/reports/presentation/pages/reports_page.dart';
import 'package:sirccd_mobile/presentation/widgets/app_shell.dart';

/// Route path constants.
abstract final class AppRoutes {
  static const splash = '/';
  static const login = '/login';
  static const home = '/home';
  static const reports = '/reports';
  static const profile = '/profile';
}

/// Listenable that notifies GoRouter when auth state changes.
/// Replace [isAuthenticated] with real auth stream in future features.
class _AuthNotifier extends ChangeNotifier {
  bool _isAuthenticated = false;

  bool get isAuthenticated => _isAuthenticated;

  // ignore: use_setters_to_change_properties
  void setAuthenticated(bool value) {
    _isAuthenticated = value;
    notifyListeners();
  }
}

/// Singleton auth notifier — wired in [AppRouter].
/// Future features inject their AuthCubit here.
final authNotifier = _AuthNotifier();

abstract final class AppRouter {
  static GoRouter get router => _router;

  static final _router = GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: authNotifier,
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

  static FutureOr<String?> _redirect(
    BuildContext context,
    GoRouterState state,
  ) {
    final isAuth = authNotifier.isAuthenticated;
    final loc = state.matchedLocation;

    // Still on splash — let SplashPage decide navigation
    if (loc == AppRoutes.splash) return null;

    // Unauthenticated trying to access protected route
    if (!isAuth && loc != AppRoutes.login) return AppRoutes.login;

    // Authenticated trying to access login
    if (isAuth && loc == AppRoutes.login) return AppRoutes.home;

    return null;
  }
}
