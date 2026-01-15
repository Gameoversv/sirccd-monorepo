from pathlib import Path
import shutil
from PIL import Image
from collections import defaultdict

def extract_bboxes_from_mask(mask_img):
    """Extrae bounding boxes de una máscara binaria sin usar numpy."""
    width, height = mask_img.size
    pixels = mask_img.load()
    
    # Encontrar regiones conectadas usando flood fill simple
    visited = set()
    regions = []
    
    def flood_fill(start_x, start_y):
        """Flood fill para encontrar región conectada."""
        stack = [(start_x, start_y)]
        region_pixels = []
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                continue
            
            if pixels[x, y] < 128:  # Background
                continue
            
            visited.add((x, y))
            region_pixels.append((x, y))
            
            # Agregar vecinos
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        
        return region_pixels
    
    # Buscar todas las regiones
    for y in range(height):
        for x in range(width):
            if pixels[x, y] >= 128 and (x, y) not in visited:
                region = flood_fill(x, y)
                if region:
                    regions.append(region)
    
    # Convertir regiones a bboxes
    bboxes = []
    for region in regions:
        if not region:
            continue
        
        xs = [p[0] for p in region]
        ys = [p[1] for p in region]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        bbox_width = max_x - min_x
        bbox_height = max_y - min_y
        
        # Filtrar bboxes muy pequeños
        if bbox_width < 10 or bbox_height < 10:
            continue
        
        # Normalizar al formato YOLO
        x_center = (min_x + max_x) / 2 / width
        y_center = (min_y + max_y) / 2 / height
        width_norm = bbox_width / width
        height_norm = bbox_height / height
        
        bboxes.append((0, x_center, y_center, width_norm, height_norm))
    
    return bboxes


def process_pothole600():
    """Procesa el dataset Pothole-600 completo."""
    RAW_DIR = Path('raw')
    PROCESSED_DIR = Path('processed/combined')
    dataset_dir = RAW_DIR / 'Pothole-600' / 'pothole600'
    
    if not dataset_dir.exists():
        print(f"❌ No se encontró el dataset en: {dataset_dir}")
        return 0
    
    processed_count = 0
    split_mapping = {'training': 'train', 'testing': 'test', 'validation': 'val'}
    
    print('Procesando Pothole-600...')
    
    for orig_split, target_split in split_mapping.items():
        rgb_dir = dataset_dir / orig_split / 'rgb'
        label_dir = dataset_dir / orig_split / 'label'
        
        if not rgb_dir.exists():
            continue
        
        images_dst = PROCESSED_DIR / 'images' / target_split
        labels_dst = PROCESSED_DIR / 'labels' / target_split
        
        images_dst.mkdir(parents=True, exist_ok=True)
        labels_dst.mkdir(parents=True, exist_ok=True)
        
        print(f'  {orig_split} → {target_split}')
        
        for img_file in rgb_dir.glob('*.png'):
            mask_file = label_dir / img_file.name
            
            if not mask_file.exists():
                print(f'    ⚠️  Máscara no encontrada: {img_file.name}')
                continue
            
            # Abrir imagen y máscara
            img = Image.open(img_file)
            mask = Image.open(mask_file).convert('L')
            
            # Extraer bboxes
            bboxes = extract_bboxes_from_mask(mask)
            
            if not bboxes:
                print(f'    ⚠️  Sin bboxes: {img_file.name}')
                continue
            
            # Copiar imagen
            dst_img = images_dst / f'pothole600_{img_file.name}'
            shutil.copy2(img_file, dst_img)
            
            # Guardar labels
            dst_label = labels_dst / f'pothole600_{img_file.stem}.txt'
            with open(dst_label, 'w') as f:
                for bbox in bboxes:
                    f.write(f'{bbox[0]} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f} {bbox[4]:.6f}\n')
            
            processed_count += 1
            if processed_count % 50 == 0:
                print(f'    Procesadas: {processed_count}')
    
    print(f'✅ Pothole-600 completado: {processed_count} imágenes')
    return processed_count


if __name__ == '__main__':
    count = process_pothole600()
    print(f'\n📊 Total procesado: {count} imágenes')
