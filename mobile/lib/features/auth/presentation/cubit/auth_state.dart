import 'package:equatable/equatable.dart';

sealed class AuthState extends Equatable {
  const AuthState();
}

final class AuthInitial extends AuthState {
  const AuthInitial();

  @override
  List<Object> get props => [];
}

final class AuthLoading extends AuthState {
  const AuthLoading();

  @override
  List<Object> get props => [];
}

final class AuthAuthenticated extends AuthState {
  const AuthAuthenticated(this.token);

  final String token;

  @override
  List<Object> get props => [token];
}

final class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();

  @override
  List<Object> get props => [];
}

final class AuthError extends AuthState {
  const AuthError(this.message);

  final String message;

  @override
  List<Object> get props => [message];
}
