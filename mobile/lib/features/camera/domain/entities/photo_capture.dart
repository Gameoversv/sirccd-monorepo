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
    this.zoomLevel,
  });

  final String imagePath;
  final DateTime timestamp;
  final DeviceOrientation orientation;
  final double? latitude;
  final double? longitude;
  final double? accuracyMeters;
  final double? zoomLevel;

  bool get hasLocation => latitude != null && longitude != null;

  double? get focalScaleFactor {
    final zoom = zoomLevel;
    if (zoom == null || zoom <= 0) return null;
    return (1 / zoom).clamp(0.25, 2.0).toDouble();
  }

  @override
  List<Object?> get props => [
    imagePath,
    timestamp,
    orientation,
    latitude,
    longitude,
    accuracyMeters,
    zoomLevel,
  ];
}
