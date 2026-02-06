"""Script rápido para verificar la anonimización."""
from PIL import Image
import random
from pathlib import Path

# Verificar imagen aleatoria de cada split
for split in ['train', 'val', 'test']:
    img_dir = Path('ml/datasets/processed/anonymized/images') / split
    images = list(img_dir.glob('*.jpg'))
    
    if images:
        sample = random.choice(images)
        img = Image.open(sample)
        
        print(f"\n{split.upper()}:")
        print(f"  Archivo: {sample.name}")
        print(f"  Tamaño: {img.size}")
        print(f"  EXIF presente: {'exif' in img.info}")
        print(f"  Info keys: {list(img.info.keys())}")

# Contar labels
print("\n📊 RESUMEN:")
for split in ['train', 'val', 'test']:
    img_count = len(list(Path(f'ml/datasets/processed/anonymized/images/{split}').glob('*.jpg')))
    label_count = len(list(Path(f'ml/datasets/processed/anonymized/labels/{split}').glob('*.txt')))
    print(f"  {split}: {img_count} imágenes, {label_count} labels")
