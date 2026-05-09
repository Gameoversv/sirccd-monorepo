import 'package:flutter/material.dart';
import 'package:sirccd_mobile/presentation/router/app_router.dart';
import 'package:sirccd_mobile/presentation/theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const SirccdApp());
}

class SirccdApp extends StatefulWidget {
  const SirccdApp({super.key});

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
    return ThemeModeScope(
      toggleTheme: _toggleTheme,
      themeMode: _themeMode,
      child: MaterialApp.router(
        title: 'SIRCCD',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: _themeMode,
        routerConfig: AppRouter.router,
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
