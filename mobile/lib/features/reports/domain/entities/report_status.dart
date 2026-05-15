enum ReportStatus {
  pending,
  processing,
  approved,
  rejected;

  static ReportStatus fromString(String value) => switch (value) {
        'pending' => pending,
        'processing' => processing,
        'approved' => approved,
        'rejected' => rejected,
        _ => pending,
      };

  String get label => switch (this) {
        ReportStatus.pending => 'Pendiente',
        ReportStatus.processing => 'Procesando',
        ReportStatus.approved => 'Aprobado',
        ReportStatus.rejected => 'Rechazado',
      };
}
