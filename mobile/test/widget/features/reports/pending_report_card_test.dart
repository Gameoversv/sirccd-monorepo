import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/pending_report.dart';
import 'package:sirccd_mobile/features/reports/domain/entities/sync_status.dart';
import 'package:sirccd_mobile/features/reports/presentation/widgets/pending_report_card.dart';

PendingReport _report({int? serverId, SyncStatus status = SyncStatus.synced}) {
  return PendingReport(
    localId: 'local-1',
    imagePath: '/no/existe.jpg',
    latitude: 18.48,
    longitude: -69.93,
    description: 'Bache en la esquina',
    syncStatus: status,
    serverId: serverId,
    createdAt: DateTime(2026, 7, 16),
  );
}

Future<void> _pumpCard(
  WidgetTester tester, {
  required PendingReport report,
  VoidCallback? onTap,
}) {
  return tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: PendingReportCard(report: report, onTap: onTap),
      ),
    ),
  );
}

void main() {
  group('PendingReportCard', () {
    testWidgets('calls onTap when the card is tapped', (tester) async {
      // Arrange
      var taps = 0;
      await _pumpCard(
        tester,
        report: _report(serverId: 42),
        onTap: () => taps++,
      );

      // Act
      await tester.tap(find.byType(PendingReportCard));
      await tester.pump();

      // Assert
      expect(taps, 1);
    });

    testWidgets('stays tappable while the report has no server id', (
      tester,
    ) async {
      // El page decide qué hacer (avisar que aún no sincroniza); la card no
      // debe tragarse el gesto.
      // Arrange
      var taps = 0;
      await _pumpCard(
        tester,
        report: _report(serverId: null, status: SyncStatus.pending),
        onTap: () => taps++,
      );

      // Act
      await tester.tap(find.byType(PendingReportCard));
      await tester.pump();

      // Assert
      expect(taps, 1);
    });

    testWidgets('dims the chevron until the report is synced', (tester) async {
      // Arrange
      await _pumpCard(tester, report: _report(serverId: null));
      final pendingChevron = tester.widget<Icon>(
        find.byIcon(Icons.chevron_right_rounded),
      );

      // Act
      await _pumpCard(tester, report: _report(serverId: 42));
      final syncedChevron = tester.widget<Icon>(
        find.byIcon(Icons.chevron_right_rounded),
      );

      // Assert
      expect(pendingChevron.color!.a, lessThan(syncedChevron.color!.a));
    });

    testWidgets('does not crash without an onTap handler', (tester) async {
      // Arrange
      await _pumpCard(tester, report: _report(serverId: 42));

      // Act
      await tester.tap(find.byType(PendingReportCard));
      await tester.pump();

      // Assert
      expect(tester.takeException(), isNull);
    });
  });
}
