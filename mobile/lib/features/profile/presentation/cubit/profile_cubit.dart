import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/core/errors/failures.dart';
import 'package:sirccd_mobile/features/profile/domain/usecases/get_current_profile_usecase.dart';
import 'package:sirccd_mobile/features/profile/presentation/cubit/profile_state.dart';

final class ProfileCubit extends Cubit<ProfileState> {
  ProfileCubit(this._getProfile) : super(const ProfileInitial());

  final GetCurrentProfileUseCase _getProfile;

  Future<void> load() async {
    emit(const ProfileLoading());
    try {
      final profile = await _getProfile();
      emit(ProfileLoaded(profile));
    } on Failure catch (f) {
      emit(ProfileError(f.message));
    } catch (_) {
      emit(const ProfileError('Error al cargar perfil.'));
    }
  }
}
