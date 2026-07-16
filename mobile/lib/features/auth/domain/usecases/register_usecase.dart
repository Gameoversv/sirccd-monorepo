import 'package:sirccd_mobile/features/auth/domain/entities/auth_token.dart';
import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';

final class RegisterUseCase {
  const RegisterUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthToken> call({
    required String username,
    required String email,
    required String password,
    String? fullName,
  }) => _repository.registerAndLogin(
    username: username,
    email: email,
    password: password,
    fullName: fullName,
  );
}
