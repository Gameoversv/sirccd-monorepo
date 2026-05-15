enum DamageType {
  bache,
  grieta;

  static DamageType? fromString(String? value) => switch (value) {
        'bache' => bache,
        'grieta' => grieta,
        _ => null,
      };

  String get label => switch (this) {
        DamageType.bache => 'Bache',
        DamageType.grieta => 'Grieta',
      };
}
