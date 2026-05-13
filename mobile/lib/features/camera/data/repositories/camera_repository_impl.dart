import 'package:camera/camera.dart';
import 'package:geolocator/geolocator.dart';
import 'package:sirccd_mobile/features/camera/data/datasources/camera_datasource.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/features/camera/domain/repositories/camera_repository.dart';

class CameraRepositoryImpl implements CameraRepository {
  const CameraRepositoryImpl(this._datasource);

  final CameraDatasource _datasource;

  @override
  Future<PhotoCapture> capturePhoto(CameraController controller) async {
    final orientation = _datasource.getOrientation(controller);

    final results = await Future.wait([
      _datasource.takePicture(controller),
      _datasource.getCurrentPosition(),
    ]);

    final xFile = results[0] as XFile;
    final position = results[1] as Position?;

    return PhotoCapture(
      imagePath: xFile.path,
      timestamp: DateTime.now(),
      orientation: orientation,
      latitude: position?.latitude,
      longitude: position?.longitude,
      accuracyMeters: position?.accuracy,
    );
  }
}
