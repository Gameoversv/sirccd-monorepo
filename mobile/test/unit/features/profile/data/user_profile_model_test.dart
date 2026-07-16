import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/profile/data/models/user_profile_model.dart';

void main() {
  group('UserProfileModel', () {
    test('parses /auth/me response', () {
      final profile = UserProfileModel.fromJson({
        'id': 19,
        'username': 'mobile_user',
        'email': 'mobile@example.com',
        'full_name': 'Mobile User',
        'phone': '+18095550123',
        'role': 'ciudadano',
        'is_active': true,
        'is_verified': false,
        'created_at': '2026-07-08T00:00:00Z',
        'updated_at': '2026-07-08T00:01:00Z',
        'last_login': '2026-07-08T00:02:00Z',
      });

      expect(profile.id, 19);
      expect(profile.displayName, 'Mobile User');
      expect(profile.roleLabel, 'Ciudadano');
      expect(profile.email, 'mobile@example.com');
      expect(profile.phone, '+18095550123');
      expect(profile.isActive, isTrue);
      expect(profile.isVerified, isFalse);
      expect(profile.lastLogin, DateTime.parse('2026-07-08T00:02:00Z'));
    });
  });
}
