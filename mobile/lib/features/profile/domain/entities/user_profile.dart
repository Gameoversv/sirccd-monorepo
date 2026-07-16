import 'package:equatable/equatable.dart';

class UserProfile extends Equatable {
  const UserProfile({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    required this.isActive,
    required this.isVerified,
    required this.createdAt,
    required this.updatedAt,
    this.fullName,
    this.phone,
    this.lastLogin,
  });

  final int id;
  final String username;
  final String email;
  final String role;
  final bool isActive;
  final bool isVerified;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? fullName;
  final String? phone;
  final DateTime? lastLogin;

  String get displayName {
    final name = fullName?.trim();
    return name == null || name.isEmpty ? username : name;
  }

  String get roleLabel => switch (role) {
    'admin' => 'Administrador',
    'supervisor' => 'Supervisor',
    'ciudadano' => 'Ciudadano',
    _ => role,
  };

  @override
  List<Object?> get props => [
    id,
    username,
    email,
    role,
    isActive,
    isVerified,
    createdAt,
    updatedAt,
    fullName,
    phone,
    lastLogin,
  ];
}
