import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/core/errors/failures.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/get_stored_token_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/login_usecase.dart';
import 'package:sirccd_mobile/features/auth/domain/usecases/logout_usecase.dart';
import 'package:sirccd_mobile/features/auth/presentation/cubit/auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._login, this._logout, this._getStoredToken)
      : super(const AuthInitial());

  final LoginUseCase _login;
  final LogoutUseCase _logout;
  final GetStoredTokenUseCase _getStoredToken;

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
}
