import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';

abstract class CameraDatasource {
  Future<XFile> takePicture(CameraController controller);
  Future<Position?> getCurrentPosition();
  DeviceOrientation getOrientation(CameraController controller);
}

class CameraDatasourceImpl implements CameraDatasource {
  @override
  Future<XFile> takePicture(CameraController controller) =>
      controller.takePicture();

  @override
  Future<Position?> getCurrentPosition() async {
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 8),
        ),
      );
    } catch (_) {
      return null;
    }
  }

  @override
  DeviceOrientation getOrientation(CameraController controller) =>
      controller.value.deviceOrientation;
}
