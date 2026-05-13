import 'package:equatable/equatable.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';

sealed class CameraState extends Equatable {
  const CameraState();
}

final class CameraIdle extends CameraState {
  const CameraIdle();
  @override
  List<Object?> get props => [];
}

final class CameraCapturing extends CameraState {
  const CameraCapturing();
  @override
  List<Object?> get props => [];
}

final class CameraCaptured extends CameraState {
  const CameraCaptured(this.capture);
  final PhotoCapture capture;
  @override
  List<Object?> get props => [capture];
}

final class CameraFailure extends CameraState {
  const CameraFailure(this.message);
  final String message;
  @override
  List<Object?> get props => [message];
}
