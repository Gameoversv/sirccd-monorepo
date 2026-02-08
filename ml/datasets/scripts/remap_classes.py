"""
Remapea clases del dataset a formato consecutivo para YOLO.

Mapeo:
  0 (bache)  → 0 (bache)
  2 (grieta) → 1 (grieta)
  4 (señal)  → ELIMINAR (fuera de alcance del proyecto)

Se aplica a labels/ y labels_severity/ en todos los splits.
"""

from pathlib import Path
from collections import Counter
from tqdm import tqdm

SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
SPLIT_DIR = SCRIPT_DIR / 'processed' / 'split'

# Mapeo: clase_original → clase_nueva (None = eliminar)
CLASS_REMAP = {
    '0': '0',   # bache → bache
    '2': '1',   # grieta → grieta
    '4': None,  # señal → eliminar
}

CLASS_NAMES = {
    '0': 'bache',
    '1': 'grieta',
}


def remap_label_file(label_path, dry_run=False):
    """Remapea un archivo de label. Retorna estadísticas."""
    stats = {'kept': 0, 'removed': 0, 'unknown': 0, 'changed': False}

    text = label_path.read_text().strip()
    if not text:
        return stats

    new_lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if not parts:
            continue

        old_class = parts[0]
        new_class = CLASS_REMAP.get(old_class)

        if new_class is None and old_class in CLASS_REMAP:
            # Clase marcada para eliminar
            stats['removed'] += 1
            stats['changed'] = True
        elif new_class is not None:
            parts[0] = new_class
            new_lines.append(' '.join(parts))
            stats['kept'] += 1
            if old_class != new_class:
                stats['changed'] = True
        else:
            # Clase desconocida - eliminar
            stats['unknown'] += 1
            stats['changed'] = True

    if not dry_run and stats['changed']:
        label_path.write_text('\n'.join(new_lines) + ('\n' if new_lines else ''))

    return stats


def process_labels_dir(labels_base, dry_run=False):
    """Procesa todos los labels en un directorio base (labels/ o labels_severity/)."""
    total = Counter()

    for split in ['train', 'val', 'test']:
        split_dir = labels_base / split
        if not split_dir.exists():
            continue

        files = list(split_dir.glob('*.txt'))
        print(f"\n  {split}: {len(files):,} archivos")

        for f in tqdm(files, desc=f"    {split}"):
            stats = remap_label_file(f, dry_run=dry_run)
            total['kept'] += stats['kept']
            total['removed'] += stats['removed']
            total['unknown'] += stats['unknown']
            if stats['changed']:
                total['files_changed'] += 1
            total['files_total'] += 1

    return total


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Remapear clases del dataset')
    parser.add_argument('--dry-run', action='store_true', help='Solo analizar, no modificar')
    args = parser.parse_args()

    mode = "ANÁLISIS" if args.dry_run else "REMAPEO"
    print("=" * 60)
    print(f"🔄 {mode} DE CLASES")
    print("=" * 60)
    print(f"\nMapeo:")
    for old, new in CLASS_REMAP.items():
        action = f"→ {new} ({CLASS_NAMES.get(new, '?')})" if new else "→ ELIMINAR"
        print(f"  Clase {old} {action}")

    if args.dry_run:
        print("\n⚠️  Modo dry-run: no se modificará ningún archivo")

    # Procesar labels/
    print(f"\n📁 Procesando labels/")
    stats_labels = process_labels_dir(SPLIT_DIR / 'labels', dry_run=args.dry_run)

    # Procesar labels_severity/
    print(f"\n📁 Procesando labels_severity/")
    stats_severity = process_labels_dir(SPLIT_DIR / 'labels_severity', dry_run=args.dry_run)

    # Resumen
    print("\n" + "=" * 60)
    print(f"✅ {mode} COMPLETADO")
    print("=" * 60)

    for name, stats in [("labels", stats_labels), ("labels_severity", stats_severity)]:
        print(f"\n  {name}/:")
        print(f"    Archivos totales:    {stats['files_total']:,}")
        print(f"    Archivos modificados:{stats['files_changed']:,}")
        print(f"    Anotaciones mantenidas: {stats['kept']:,}")
        print(f"    Anotaciones eliminadas: {stats['removed']:,}")
        if stats['unknown']:
            print(f"    Clases desconocidas:    {stats['unknown']:,}")

    total_kept = stats_labels['kept'] + stats_severity['kept']
    total_removed = stats_labels['removed'] + stats_severity['removed']
    print(f"\n  TOTAL:")
    print(f"    Mantenidas: {total_kept:,}")
    print(f"    Eliminadas: {total_removed:,}")


if __name__ == '__main__':
    main()
