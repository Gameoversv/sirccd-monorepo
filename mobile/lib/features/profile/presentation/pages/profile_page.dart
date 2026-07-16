import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_cubit.dart';
import 'package:sirccd_mobile/features/profile/domain/entities/user_profile.dart';
import 'package:sirccd_mobile/features/profile/presentation/cubit/profile_cubit.dart';
import 'package:sirccd_mobile/features/profile/presentation/cubit/profile_state.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => di<ProfileCubit>()..load(),
      child: const _ProfileView(),
    );
  }
}

class _ProfileView extends StatelessWidget {
  const _ProfileView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: ListView(
        children: [
          const SizedBox(height: 24),
          BlocBuilder<ProfileCubit, ProfileState>(
            builder: (context, state) => switch (state) {
              ProfileInitial() || ProfileLoading() => const _LoadingHeader(),
              ProfileLoaded(:final profile) => _ProfileHeader(profile: profile),
              ProfileError(:final message) => _ErrorHeader(message: message),
            },
          ),
          const Divider(height: 32),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Cerrar sesión'),
            onTap: () => context.read<AuthCubit>().logout(),
          ),
        ],
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.profile});

  final UserProfile profile;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 32,
                backgroundColor: colorScheme.primaryContainer,
                child: Text(
                  _initials(profile),
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      profile.displayName,
                      style: theme.textTheme.titleMedium,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      profile.email,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _InfoTile(
            icon: Icons.badge_outlined,
            label: 'Usuario',
            value: profile.username,
          ),
          _InfoTile(
            icon: Icons.verified_user_outlined,
            label: 'Rol',
            value: profile.roleLabel,
          ),
          if (profile.phone != null && profile.phone!.isNotEmpty)
            _InfoTile(
              icon: Icons.phone_outlined,
              label: 'Teléfono',
              value: profile.phone!,
            ),
          _InfoTile(
            icon: profile.isVerified
                ? Icons.check_circle_outline
                : Icons.info_outline,
            label: 'Verificación',
            value: profile.isVerified ? 'Verificado' : 'Pendiente',
          ),
        ],
      ),
    );
  }

  String _initials(UserProfile profile) {
    final parts = profile.displayName
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .toList();
    if (parts.isEmpty) return '?';
    final first = parts.first.substring(0, 1);
    final second = parts.length > 1 ? parts.last.substring(0, 1) : '';
    return (first + second).toUpperCase();
  }
}

class _InfoTile extends StatelessWidget {
  const _InfoTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Row(
        children: [
          Icon(icon, size: 20, color: colorScheme.onSurfaceVariant),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  ),
                ),
                Text(value, style: theme.textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingHeader extends StatelessWidget {
  const _LoadingHeader();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Center(child: CircularProgressIndicator()),
    );
  }
}

class _ErrorHeader extends StatelessWidget {
  const _ErrorHeader({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          Icon(Icons.error_outline, color: colorScheme.error, size: 40),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () => context.read<ProfileCubit>().load(),
            icon: const Icon(Icons.refresh),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}
