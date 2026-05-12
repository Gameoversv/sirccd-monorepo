import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_cubit.dart';
import 'package:sirccd_mobile/presentation/router/app_router.dart';
import 'package:sirccd_mobile/presentation/theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initDependencies();

  final authCubit = di<AuthCubit>();
  final appRouter = AppRouter(authCubit);

  runApp(SirccdApp(authCubit: authCubit, router: appRouter.router));
}

class SirccdApp extends StatefulWidget {
  const SirccdApp({
    required this.authCubit,
    required this.router,
    super.key,
  });

  final AuthCubit authCubit;
  final GoRouter router;

  @override
  State<SirccdApp> createState() => _SirccdAppState();
}

class _SirccdAppState extends State<SirccdApp> {
  ThemeMode _themeMode = ThemeMode.system;

  void _toggleTheme() {
    setState(() {
      _themeMode =
          _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: widget.authCubit,
      child: ThemeModeScope(
        toggleTheme: _toggleTheme,
        themeMode: _themeMode,
        child: MaterialApp.router(
          title: 'SIRCCD',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          themeMode: _themeMode,
          routerConfig: widget.router,
        ),
      ),
    );
  }
}

/// Exposes theme toggle to any descendant via [ThemeModeScope.of].
class ThemeModeScope extends InheritedWidget {
  const ThemeModeScope({
    required this.toggleTheme,
    required this.themeMode,
    required super.child,
    super.key,
  });

  final VoidCallback toggleTheme;
  final ThemeMode themeMode;

  static ThemeModeScope? of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<ThemeModeScope>();

  @override
  bool updateShouldNotify(ThemeModeScope old) => themeMode != old.themeMode;
}
