import 'package:flutter/material.dart';
import 'package:sirccd_mobile/presentation/theme/app_colors.dart';

class CameraGuideOverlay extends StatelessWidget {
  const CameraGuideOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        CustomPaint(painter: _GuidePainter()),
        Positioned(
          bottom: 120,
          left: 0,
          right: 0,
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'Centra el daño vial en el recuadro',
                style: TextStyle(color: Colors.white, fontSize: 13),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _GuidePainter extends CustomPainter {
  static const double _bracketLength = 28.0;
  static const double _bracketWidth = 3.5;

  @override
  void paint(Canvas canvas, Size size) {
    final guideRect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2 - 20),
      width: size.width * 0.78,
      height: size.width * 0.78,
    );

    final overlayPaint = Paint()..color = Colors.black.withValues(alpha: 0.55);

    // Four dark regions surrounding the guide rect
    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, guideRect.top),
      overlayPaint,
    );
    canvas.drawRect(
      Rect.fromLTWH(0, guideRect.top, guideRect.left, guideRect.height),
      overlayPaint,
    );
    canvas.drawRect(
      Rect.fromLTWH(
        guideRect.right,
        guideRect.top,
        size.width - guideRect.right,
        guideRect.height,
      ),
      overlayPaint,
    );
    canvas.drawRect(
      Rect.fromLTWH(
        0,
        guideRect.bottom,
        size.width,
        size.height - guideRect.bottom,
      ),
      overlayPaint,
    );

    // Corner brackets
    final bracketPaint = Paint()
      ..color = AppColors.primary
      ..strokeWidth = _bracketWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    _drawCorner(canvas, bracketPaint, guideRect.topLeft, 1, 1);
    _drawCorner(canvas, bracketPaint, guideRect.topRight, -1, 1);
    _drawCorner(canvas, bracketPaint, guideRect.bottomLeft, 1, -1);
    _drawCorner(canvas, bracketPaint, guideRect.bottomRight, -1, -1);

    // Subtle center crosshair
    final crossPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.35)
      ..strokeWidth = 1.0;
    final c = guideRect.center;
    canvas.drawLine(c - const Offset(10, 0), c + const Offset(10, 0), crossPaint);
    canvas.drawLine(c - const Offset(0, 10), c + const Offset(0, 10), crossPaint);
  }

  void _drawCorner(
    Canvas canvas,
    Paint paint,
    Offset corner,
    double dx,
    double dy,
  ) {
    canvas.drawLine(
      corner,
      corner + Offset(_bracketLength * dx, 0),
      paint,
    );
    canvas.drawLine(
      corner,
      corner + Offset(0, _bracketLength * dy),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
