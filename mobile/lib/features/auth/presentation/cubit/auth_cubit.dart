import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/core/errors/failures.dart';
import 'package:sirccd_mobile/core/services/session_service.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/get_stored_token_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/login_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/logout_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/register_usecase.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(
    this._login,
    this._register,
    this._logout,
    this._getStoredToken,
    this._session,
  ) : super(const AuthInitial()) {
    _sessionSub = _session.expired.listen(
      (event) => unawaited(_expireSession(event.message)),
    );
  }

  final LoginUseCase _login;
  final RegisterUseCase _register;
  final LogoutUseCase _logout;
  final GetStoredTokenUseCase _getStoredToken;
  final SessionService _session;
  late final StreamSubscription<SessionExpiredEvent> _sessionSub;

  Future<void> checkStoredToken() async {
    emit(const AuthLoading());
    try {
      final token = await _getStoredToken();
      emit(
        token != null
            ? AuthAuthenticated(token.accessToken)
            : const AuthUnauthenticated(),
      );
    } on Failure catch (_) {
      emit(const AuthUnauthenticated());
    } catch (_) {
      emit(const AuthUnauthenticated());
    }
  }

  Future<void> register({
    required String username,
    required String email,
    required String password,
    String? fullName,
  }) async {
    emit(const AuthLoading());
    try {
      final token = await _register(
        username: username,
        email: email,
        password: password,
        fullName: fullName,
      );
      emit(AuthAuthenticated(token.accessToken));
    } on Failure catch (f) {
      emit(AuthError(f.message));
    } catch (_) {
      emit(const AuthError('Error inesperado.'));
    }
  }

  Future<void> login(String email, String password) async {
    emit(const AuthLoading());
    try {
      final token = await _login(email, password);
      emit(AuthAuthenticated(token.accessToken));
    } on Failure catch (f) {
      emit(AuthError(f.message));
    } catch (_) {
      emit(const AuthError('Error inesperado.'));
    }
  }

  Future<void> logout() async {
    await _logout();
    emit(const AuthUnauthenticated());
  }

  Future<void> _expireSession(String message) async {
    if (isClosed || state is AuthUnauthenticated || state is AuthExpired) {
      return;
    }
    try {
      await _logout();
    } catch (_) {
      // The local token is best-effort cleanup here; redirect still matters.
    }
    if (!isClosed) emit(AuthExpired(message));
  }

  @override
  Future<void> close() async {
    await _sessionSub.cancel();
    return super.close();
  }
}
