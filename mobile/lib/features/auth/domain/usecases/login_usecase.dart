import 'package:sirccd_mobile/features/auth/domain/entities/auth_token.dart';
import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';

final class LoginUseCase {
  const LoginUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthToken> call(String email, String password) =>
      _repository.login(email, password);
}
