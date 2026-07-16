import 'package:sirccd_mobile/features/profile/domain/entities/user_profile.dart';
import 'package:sirccd_mobile/features/profile/domain/repositories/profile_repository.dart';

final class GetCurrentProfileUseCase {
  const GetCurrentProfileUseCase(this._repository);

  final ProfileRepository _repository;

  Future<UserProfile> call() => _repository.getCurrentUser();
}
