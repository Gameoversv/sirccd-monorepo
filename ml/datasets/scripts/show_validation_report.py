import json
from pathlib import Path

report_path = Path('ml/datasets/metadata/validation_report.json')
with open(report_path, 'r', encoding='utf-8') as f:
    report = json.load(f)

print("=" * 70)
print("📊 RESUMEN DE VALIDACIÓN DEL DATASET")
print("=" * 70)

print(f"\n🎯 Estado: {report['validation_status']}")
print(f"⏰ Timestamp: {report['timestamp']}")

s = report['summary']

print(f"\n🖼️  Imágenes:")
print(f"   Total: {s['total_images']:,}")
print(f"   Válidas: {s['valid_images']:,} ({s['valid_images']/s['total_images']*100:.2f}%)")
print(f"   Inválidas: {s['invalid_images']:,}")
print(f"   Corruptas: {s['corrupted_images']:,}")

print(f"\n🏷️  Labels:")
print(f"   Faltantes: {s['missing_labels']:,}")
print(f"   Vacíos: {s['empty_labels']:,}")

print(f"\n📦 Anotaciones:")
print(f"   Total: {s['total_annotations']:,}")
print(f"   Baches: {s['annotations_by_class']['bache']:,} ({s['annotations_by_class']['bache']/s['total_annotations']*100:.1f}%)")
print(f"   Grietas: {s['annotations_by_class']['grieta']:,} ({s['annotations_by_class']['grieta']/s['total_annotations']*100:.1f}%)")

print(f"\n⚠️  Errores:")
print(f"   Críticos: {s['total_errors']['critical']:,}")
print(f"   Advertencias: {s['total_errors']['warning']:,}")
print(f"   Info: {s['total_errors']['info']:,}")

print(f"\n📊 Por split:")
for split_name, stats in report['splits'].items():
    print(f"\n   {split_name.upper()}:")
    print(f"      Imágenes: {stats['total_images']:,}")
    print(f"      Anotaciones: {stats['total_annotations']:,}")
    print(f"      Errores críticos: {len(stats['errors']['critical']):,}")
    print(f"      Advertencias: {len(stats['errors']['warning']):,}")

if s['total_errors']['critical'] > 0:
    print(f"\n❌ Validación FALLÓ - Hay {s['total_errors']['critical']} errores críticos")
else:
    print(f"\n✅ Validación EXITOSA - Dataset íntegro")
