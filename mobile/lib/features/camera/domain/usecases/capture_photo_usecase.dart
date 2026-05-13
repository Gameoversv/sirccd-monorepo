import 'package:camera/camera.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/features/camera/domain/repositories/camera_repository.dart';

class CapturePhotoUseCase {
  const CapturePhotoUseCase(this._repository);

  final CameraRepository _repository;

  Future<PhotoCapture> call(CameraController controller) =>
      _repository.capturePhoto(controller);
}
