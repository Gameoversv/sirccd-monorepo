import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/profile/domain/entities/user_profile.dart';

sealed class ProfileState extends Equatable {
  const ProfileState();
}

final class ProfileInitial extends ProfileState {
  const ProfileInitial();

  @override
  List<Object?> get props => [];
}

final class ProfileLoading extends ProfileState {
  const ProfileLoading();

  @override
  List<Object?> get props => [];
}

final class ProfileLoaded extends ProfileState {
  const ProfileLoaded(this.profile);

  final UserProfile profile;

  @override
  List<Object?> get props => [profile];
}

final class ProfileError extends ProfileState {
  const ProfileError(this.message);

  final String message;

  @override
  List<Object?> get props => [message];
}
