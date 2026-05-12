import 'package:permission_handler/permission_handler.dart';

class PermissionService {
  Future<PermissionStatus> locationStatus() =>
      Permission.locationWhenInUse.status;

  Future<PermissionStatus> cameraStatus() => Permission.camera.status;

  Future<PermissionStatus> requestLocation() =>
      Permission.locationWhenInUse.request();

  Future<PermissionStatus> requestCamera() => Permission.camera.request();

  Future<void> openSettings() => openAppSettings();
}
