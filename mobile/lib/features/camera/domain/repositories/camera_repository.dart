import 'package:camera/camera.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';

abstract class CameraRepository {
  Future<PhotoCapture> capturePhoto(CameraController controller);
}
