import 'package:camera/camera.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/features/camera/domain/usecases/capture_photo_usecase.dart';
import 'package:sirccd_mobile/features/camera/presentation/cubit/camera_state.dart';

class CameraCubit extends Cubit<CameraState> {
  CameraCubit(this._capturePhoto) : super(const CameraIdle());

  final CapturePhotoUseCase _capturePhoto;

  Future<void> capture(CameraController controller, {double? zoomLevel}) async {
    if (state is CameraCapturing) return;
    emit(const CameraCapturing());
    try {
      final capture = await _capturePhoto(controller, zoomLevel: zoomLevel);
      emit(CameraCaptured(capture));
    } catch (e) {
      emit(CameraFailure(e.toString()));
    }
  }

  void retake() => emit(const CameraIdle());
}
