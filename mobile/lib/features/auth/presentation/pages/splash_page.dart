import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_cubit.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future<void>.delayed(const Duration(milliseconds: 1500));
    if (!mounted) return;
    // Router's refreshListenable handles navigation once state changes.
    context.read<AuthCubit>().checkStoredToken();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.primary,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.location_city, size: 72, color: colorScheme.onPrimary),
            const SizedBox(height: 16),
            Text(
              'SIRCCD',
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    color: colorScheme.onPrimary,
                    letterSpacing: 4,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Reporta. Mejora. Transforma.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: colorScheme.onPrimary.withValues(alpha: 0.8),
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
