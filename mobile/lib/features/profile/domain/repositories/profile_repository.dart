import 'package:sirccd_mobile/features/profile/domain/entities/user_profile.dart';

abstract interface class ProfileRepository {
  Future<UserProfile> getCurrentUser();
}
