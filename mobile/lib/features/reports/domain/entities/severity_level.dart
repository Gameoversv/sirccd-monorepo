enum SeverityLevel {
  baja,
  media,
  alta;

  static SeverityLevel? fromString(String? value) => switch (value) {
        'baja' => baja,
        'media' => media,
        'alta' => alta,
        _ => null,
      };

  String get label => switch (this) {
        SeverityLevel.baja => 'Baja',
        SeverityLevel.media => 'Media',
        SeverityLevel.alta => 'Alta',
      };
}
