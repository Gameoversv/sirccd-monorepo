import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';

final class LogoutUseCase {
  const LogoutUseCase(this._repository);

  final AuthRepository _repository;

  Future<void> call() => _repository.logout();
}
