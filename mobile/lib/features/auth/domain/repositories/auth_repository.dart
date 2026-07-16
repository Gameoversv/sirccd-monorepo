import 'package:sirccd_mobile/features/auth/domain/entities/auth_token.dart';

abstract interface class AuthRepository {
  Future<AuthToken> login(String email, String password);
  Future<AuthToken> registerAndLogin({
    required String username,
    required String email,
    required String password,
    String? fullName,
  });
  Future<void> logout();
  Future<AuthToken?> getStoredToken();
}
