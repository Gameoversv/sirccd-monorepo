import 'package:flutter/material.dart';

/// SIRCCD brand colors — primary is urban/civic blue-green, warning is alert amber.
abstract final class AppColors {
  // Primary — civic blue
  static const primary = Color(0xFF1A6B8A);
  static const primaryContainer = Color(0xFFB3E0F2);
  static const onPrimary = Color(0xFFFFFFFF);
  static const onPrimaryContainer = Color(0xFF00344A);

  // Secondary — urban teal
  static const secondary = Color(0xFF2E8B74);
  static const secondaryContainer = Color(0xFFB2DFDB);
  static const onSecondary = Color(0xFFFFFFFF);
  static const onSecondaryContainer = Color(0xFF00382E);

  // Error / alert
  static const error = Color(0xFFBA1A1A);
  static const errorContainer = Color(0xFFFFDAD6);
  static const onError = Color(0xFFFFFFFF);
  static const onErrorContainer = Color(0xFF410002);

  // Warning — road hazard amber
  static const warning = Color(0xFFF59E0B);
  static const warningContainer = Color(0xFFFEF3C7);

  // Neutral surfaces (light)
  static const surface = Color(0xFFF8FAFB);
  static const surfaceVariant = Color(0xFFDCE8ED);
  static const onSurface = Color(0xFF191C1E);
  static const onSurfaceVariant = Color(0xFF404849);
  static const outline = Color(0xFF70787C);
  static const outlineVariant = Color(0xFFC0C8CC);

  // Neutral surfaces (dark)
  static const surfaceDark = Color(0xFF101416);
  static const surfaceVariantDark = Color(0xFF2A3234);
  static const onSurfaceDark = Color(0xFFE0E3E5);
  static const onSurfaceVariantDark = Color(0xFFBEC7CB);
  static const outlineDark = Color(0xFF8A9296);
  static const outlineVariantDark = Color(0xFF3D4547);

  // Status colors (report states)
  static const statusPending = Color(0xFFF59E0B);
  static const statusInProgress = Color(0xFF3B82F6);
  static const statusResolved = Color(0xFF22C55E);
  static const statusRejected = Color(0xFFEF4444);
}
