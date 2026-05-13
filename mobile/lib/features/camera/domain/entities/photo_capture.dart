import 'package:equatable/equatable.dart';
import 'package:flutter/services.dart';

class PhotoCapture extends Equatable {
  const PhotoCapture({
    required this.imagePath,
    required this.timestamp,
    required this.orientation,
    this.latitude,
    this.longitude,
    this.accuracyMeters,
  });

  final String imagePath;
  final DateTime timestamp;
  final DeviceOrientation orientation;
  final double? latitude;
  final double? longitude;
  final double? accuracyMeters;

  bool get hasLocation => latitude != null && longitude != null;

  @override
  List<Object?> get props => [
        imagePath,
        timestamp,
        orientation,
        latitude,
        longitude,
        accuracyMeters,
      ];
}
