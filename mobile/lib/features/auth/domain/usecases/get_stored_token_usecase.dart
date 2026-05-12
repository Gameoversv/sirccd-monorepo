import 'package:sirccd_mobile/features/auth/domain/entities/auth_token.dart';
import 'package:sirccd_mobile/features/auth/domain/repositories/auth_repository.dart';

final class GetStoredTokenUseCase {
  const GetStoredTokenUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthToken?> call() => _repository.getStoredToken();
}
