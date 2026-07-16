import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sirccd_mobile/core/di/injection.dart';
import 'package:sirccd_mobile/features/camera/domain/entities/photo_capture.dart';
import 'package:sirccd_mobile/features/camera/presentation/cubit/camera_cubit.dart';
import 'package:sirccd_mobile/features/camera/presentation/cubit/camera_state.dart';
import 'package:sirccd_mobile/features/camera/presentation/widgets/camera_guide_overlay.dart';
import 'package:sirccd_mobile/features/camera/presentation/widgets/photo_preview.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class CameraPage extends StatefulWidget {
  const CameraPage({super.key, this.onPhotoAccepted});

  /// Called with the accepted capture when user taps "Usar foto".
  final ValueChanged<PhotoCapture>? onPhotoAccepted;

  @override
  State<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends State<CameraPage> with WidgetsBindingObserver {
  List<CameraDescription> _cameras = [];
  CameraController? _controller;
  int _cameraIndex = 0;
  FlashMode _flashMode = FlashMode.off;
  bool _isInitialized = false;
  String? _initError;
  double _minZoomLevel = 1;
  double _maxZoomLevel = 1;
  double _zoomLevel = 1;
  double _baseZoomLevel = 1;

  @override
  void initState() {
    super.initState();
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
    WidgetsBinding.instance.addObserver(this);
    _initCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    SystemChrome.setPreferredOrientations(DeviceOrientation.values);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final ctrl = _controller;
    if (ctrl == null || !ctrl.value.isInitialized) return;
    if (state == AppLifecycleState.inactive) {
      ctrl.dispose();
      setState(() => _isInitialized = false);
    } else if (state == AppLifecycleState.resumed) {
      _initCamera();
    }
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras.isEmpty) {
        setState(() => _initError = 'No se encontró cámara disponible.');
        return;
      }
      final backIndex = _cameras.indexWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
      );
      _cameraIndex = backIndex != -1 ? backIndex : 0;
      await _mountCamera(_cameraIndex);
    } catch (e) {
      setState(() => _initError = e.toString());
    }
  }

  Future<void> _mountCamera(int index) async {
    await _controller?.dispose();
    final ctrl = CameraController(
      _cameras[index],
      ResolutionPreset.high,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );
    _controller = ctrl;
    await ctrl.initialize();
    if (!mounted) return;
    await ctrl.setFlashMode(_flashMode);
    var minZoom = 1.0;
    var maxZoom = 1.0;
    var nextZoom = 1.0;
    try {
      minZoom = await ctrl.getMinZoomLevel();
      maxZoom = await ctrl.getMaxZoomLevel();
      nextZoom = _clampZoom(_zoomLevel, minZoom, maxZoom);
      await ctrl.setZoomLevel(nextZoom);
    } on Exception {
      minZoom = 1.0;
      maxZoom = 1.0;
      nextZoom = 1.0;
    }
    setState(() {
      _cameraIndex = index;
      _isInitialized = true;
      _initError = null;
      _minZoomLevel = minZoom;
      _maxZoomLevel = maxZoom;
      _zoomLevel = nextZoom;
    });
  }

  bool get _supportsZoom => (_maxZoomLevel - _minZoomLevel) > 0.01;

  double _clampZoom(double value, double min, double max) {
    if (max <= min) return min;
    return value.clamp(min, max).toDouble();
  }

  Future<void> _setZoom(double value) async {
    final ctrl = _controller;
    if (ctrl == null || !ctrl.value.isInitialized) return;

    final nextZoom = _clampZoom(value, _minZoomLevel, _maxZoomLevel);
    try {
      await ctrl.setZoomLevel(nextZoom);
      if (mounted) setState(() => _zoomLevel = nextZoom);
    } on Exception {
      // Some devices briefly reject zoom changes while refocusing.
    }
  }

  void _handleScaleStart(ScaleStartDetails details) {
    _baseZoomLevel = _zoomLevel;
  }

  void _handleScaleUpdate(ScaleUpdateDetails details) {
    if (details.pointerCount < 2) return;
    unawaited(_setZoom(_baseZoomLevel * details.scale));
  }

  Future<void> _toggleFlash() async {
    final next = _flashMode == FlashMode.off ? FlashMode.torch : FlashMode.off;
    await _controller?.setFlashMode(next);
    if (mounted) setState(() => _flashMode = next);
  }

  Future<void> _flipCamera() async {
    if (_cameras.length < 2) return;
    await _mountCamera((_cameraIndex + 1) % _cameras.length);
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => di<CameraCubit>(),
      child: Scaffold(
        backgroundColor: Colors.black,
        body: BlocConsumer<CameraCubit, CameraState>(
          listener: (context, state) {
            if (state is CameraFailure) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(state.message),
                  backgroundColor: AppColors.error,
                ),
              );
            }
          },
          builder: (context, state) {
            if (state is CameraCaptured) {
              return PhotoPreview(
                capture: state.capture,
                onRetake: context.read<CameraCubit>().retake,
                onAccept: (capture) {
                  widget.onPhotoAccepted?.call(capture);
                  Navigator.of(context).pop(capture);
                },
              );
            }

            return Stack(
              fit: StackFit.expand,
              children: [
                GestureDetector(
                  onScaleStart: _supportsZoom ? _handleScaleStart : null,
                  onScaleUpdate: _supportsZoom ? _handleScaleUpdate : null,
                  child: _buildPreview(context),
                ),
                if (_isInitialized && state is! CameraCapturing)
                  const CameraGuideOverlay(),
                if (_isInitialized &&
                    state is! CameraCapturing &&
                    _supportsZoom)
                  _ZoomControl(
                    zoomLevel: _zoomLevel,
                    minZoomLevel: _minZoomLevel,
                    maxZoomLevel: _maxZoomLevel,
                    onChanged: (value) => _setZoom(value),
                  ),
                if (state is CameraCapturing) _CapturingShimmer(),
                _TopBar(
                  flashMode: _flashMode,
                  onFlash: _toggleFlash,
                  onClose: () => Navigator.of(context).pop(),
                ),
                _BottomBar(
                  isCapturing: state is CameraCapturing,
                  isReady: _isInitialized,
                  hasFrontCamera: _cameras.length > 1,
                  onCapture: _isInitialized && state is! CameraCapturing
                      ? () => context.read<CameraCubit>().capture(
                          _controller!,
                          zoomLevel: _zoomLevel,
                        )
                      : null,
                  onFlip: _flipCamera,
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildPreview(BuildContext context) {
    if (_initError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            _initError!,
            style: const TextStyle(color: Colors.white70),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    if (!_isInitialized || _controller == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    return _ScaledPreview(controller: _controller!);
  }
}

class _ScaledPreview extends StatelessWidget {
  const _ScaledPreview({required this.controller});
  final CameraController controller;

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final scale = (() {
      final previewRatio = controller.value.aspectRatio;
      final screenRatio = size.width / size.height;
      if (previewRatio < screenRatio) {
        return size.width / (size.height * previewRatio);
      }
      return size.height / (size.width / previewRatio);
    })();

    return Transform.scale(
      scale: scale,
      child: Center(child: CameraPreview(controller)),
    );
  }
}

class _CapturingShimmer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black.withValues(alpha: 0.45),
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: AppColors.primary),
            SizedBox(height: 16),
            Text(
              'Capturando…',
              style: TextStyle(color: Colors.white70, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({
    required this.flashMode,
    required this.onFlash,
    required this.onClose,
  });

  final FlashMode flashMode;
  final VoidCallback onFlash;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.close_rounded),
                color: Colors.white,
                onPressed: onClose,
              ),
              IconButton(
                icon: Icon(
                  flashMode == FlashMode.off
                      ? Icons.flash_off_rounded
                      : Icons.flash_on_rounded,
                ),
                color: flashMode == FlashMode.off
                    ? Colors.white70
                    : AppColors.warning,
                onPressed: onFlash,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ZoomControl extends StatelessWidget {
  const _ZoomControl({
    required this.zoomLevel,
    required this.minZoomLevel,
    required this.maxZoomLevel,
    required this.onChanged,
  });

  final double zoomLevel;
  final double minZoomLevel;
  final double maxZoomLevel;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    final value = zoomLevel.clamp(minZoomLevel, maxZoomLevel).toDouble();
    final presets = [1.0, 2.0]
        .where((v) => v >= minZoomLevel - 0.01 && v <= maxZoomLevel + 0.01)
        .toList();

    return Positioned(
      left: 20,
      right: 20,
      bottom: MediaQuery.of(context).padding.bottom + 120,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.62),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.white.withValues(alpha: 0.14)),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
          child: Row(
            children: [
              Container(
                width: 48,
                alignment: Alignment.center,
                padding: const EdgeInsets.symmetric(vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '${value.toStringAsFixed(1)}x',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              if (presets.isNotEmpty) ...[
                for (final preset in presets) ...[
                  _ZoomPresetButton(
                    value: preset,
                    selected: (value - preset).abs() < 0.05,
                    onSelected: onChanged,
                  ),
                  const SizedBox(width: 6),
                ],
              ],
              Expanded(
                child: SliderTheme(
                  data: SliderTheme.of(context).copyWith(
                    trackHeight: 3,
                    thumbShape: const RoundSliderThumbShape(
                      enabledThumbRadius: 7,
                    ),
                    overlayShape: const RoundSliderOverlayShape(
                      overlayRadius: 14,
                    ),
                  ),
                  child: Slider(
                    value: value,
                    min: minZoomLevel,
                    max: maxZoomLevel,
                    activeColor: AppColors.primary,
                    inactiveColor: Colors.white.withValues(alpha: 0.28),
                    onChanged: onChanged,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ZoomPresetButton extends StatelessWidget {
  const _ZoomPresetButton({
    required this.value,
    required this.selected,
    required this.onSelected,
  });

  final double value;
  final bool selected;
  final ValueChanged<double> onSelected;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(6),
      onTap: () => onSelected(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.primary
              : Colors.white.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          '${value.toStringAsFixed(0)}x',
          style: TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar({
    required this.isCapturing,
    required this.isReady,
    required this.hasFrontCamera,
    required this.onCapture,
    required this.onFlip,
  });

  final bool isCapturing;
  final bool isReady;
  final bool hasFrontCamera;
  final VoidCallback? onCapture;
  final VoidCallback onFlip;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: 0,
      left: 0,
      right: 0,
      child: Container(
        padding: EdgeInsets.fromLTRB(
          32,
          20,
          32,
          MediaQuery.of(context).padding.bottom + 20,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.bottomCenter,
            end: Alignment.topCenter,
            colors: [Colors.black.withValues(alpha: 0.75), Colors.transparent],
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Placeholder to balance layout
            const SizedBox(width: 48),
            _CaptureButton(onTap: onCapture, isCapturing: isCapturing),
            if (hasFrontCamera)
              IconButton(
                icon: const Icon(Icons.flip_camera_android_rounded),
                color: Colors.white,
                iconSize: 28,
                onPressed: isCapturing ? null : onFlip,
              )
            else
              const SizedBox(width: 48),
          ],
        ),
      ),
    );
  }
}

class _CaptureButton extends StatelessWidget {
  const _CaptureButton({required this.onTap, required this.isCapturing});

  final VoidCallback? onTap;
  final bool isCapturing;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 120),
        width: 72,
        height: 72,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: isCapturing ? AppColors.primary : Colors.white,
            width: 3.5,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(6),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 120),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isCapturing ? AppColors.primary : Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
