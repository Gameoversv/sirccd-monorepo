#!/usr/bin/env python3
"""
Script para verificar el estado del entrenamiento guardado en Google Drive
y preparar para continuar el entrenamiento.

Uso:
    python check_training_status.py --drive-path "/ruta/a/Google Drive"
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

def check_model_files(drive_path):
    """Verificar que existan los archivos del modelo."""
    models_path = Path(drive_path) / "SIRCCD_Models" / "train" / "weights"
    
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE ARCHIVOS DE MODELO")
    print("=" * 70)
    
    files_to_check = {
        'best.pt': 'Mejor modelo (mayor mAP)',
        'last.pt': 'Último checkpoint (para continuar)',
    }
    
    found_files = {}
    missing_files = []
    
    for filename, description in files_to_check.items():
        file_path = models_path / filename
        if file_path.exists():
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            found_files[filename] = {
                'path': str(file_path),
                'size_mb': file_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
            }
            print(f"✅ {filename:12} - {description}")
            print(f"   Ruta:     {file_path}")
            print(f"   Tamaño:   {file_size:.2f} MB")
            print(f"   Modificado: {found_files[filename]['modified']}")
        else:
            missing_files.append(filename)
            print(f"❌ {filename:12} - NO ENCONTRADO")
            print(f"   Se esperaba en: {file_path}")
    
    print()
    return found_files, missing_files

def check_dataset(drive_path):
    """Verificar que exista el dataset."""
    dataset_path = Path(drive_path) / "SIRCCD_Dataset" / "sirccd_dataset_v1.0.0.zip"
    
    print("=" * 70)
    print("📦 VERIFICACIÓN DE DATASET")
    print("=" * 70)
    
    if dataset_path.exists():
        file_size = dataset_path.stat().st_size / (1024 * 1024 * 1024)  # GB
        print(f"✅ Dataset encontrado")
        print(f"   Ruta:   {dataset_path}")
        print(f"   Tamaño: {file_size:.2f} GB")
        print()
        return True
    else:
        print(f"❌ Dataset NO encontrado")
        print(f"   Se esperaba en: {dataset_path}")
        print()
        return False

def parse_results_csv(drive_path):
    """Parsear archivo results.csv para obtener métricas del último epoch."""
    results_path = Path(drive_path) / "SIRCCD_Models" / "train" / "results.csv"
    
    print("=" * 70)
    print("📊 ANÁLISIS DE MÉTRICAS DE ENTRENAMIENTO")
    print("=" * 70)
    
    if not results_path.exists():
        print(f"❌ No se encontró results.csv en {results_path}")
        print()
        return None
    
    try:
        # Leer última línea del CSV (último epoch)
        with open(results_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:  # Header + al menos 1 epoch
            print("❌ results.csv vacío o corrupto")
            return None
        
        # Header y última línea
        header = lines[0].strip().split(',')
        last_epoch_data = lines[-1].strip().split(',')
        
        # Crear diccionario
        metrics = dict(zip(header, last_epoch_data))
        
        # Extraer métricas clave
        epoch = int(float(metrics.get('epoch', 0)))
        map50 = float(metrics.get('metrics/mAP50(B)', 0))
        map50_95 = float(metrics.get('metrics/mAP50-95(B)', 0))
        precision = float(metrics.get('metrics/precision(B)', 0))
        recall = float(metrics.get('metrics/recall(B)', 0))
        
        print(f"📈 Último Epoch Completado: {epoch}")
        print(f"\n🎯 Métricas de Validación:")
        print(f"   mAP50:     {map50:.4f} ({map50*100:.2f}%)")
        print(f"   mAP50-95:  {map50_95:.4f} ({map50_95*100:.2f}%)")
        print(f"   Precision: {precision:.4f} ({precision*100:.2f}%)")
        print(f"   Recall:    {recall:.4f} ({recall*100:.2f}%)")
        
        # Progreso
        total_epochs = 100  # Asumido
        progress_pct = (epoch / total_epochs) * 100
        progress_bar = "█" * int(progress_pct / 2) + "░" * (50 - int(progress_pct / 2))
        
        print(f"\n⏱️  Progreso: [{progress_bar}] {progress_pct:.1f}%")
        print(f"   Epochs completados: {epoch}/{total_epochs}")
        print(f"   Epochs restantes:   {total_epochs - epoch}")
        
        print()
        
        return {
            'epoch': epoch,
            'map50': map50,
            'map50_95': map50_95,
            'precision': precision,
            'recall': recall,
            'total_epochs': total_epochs
        }
        
    except Exception as e:
        print(f"❌ Error al parsear results.csv: {e}")
        return None

def analyze_training_plots(drive_path):
    """Verificar que existan las gráficas de entrenamiento."""
    plots_path = Path(drive_path) / "SIRCCD_Models" / "train"
    
    print("=" * 70)
    print("📈 GRÁFICAS DE ENTRENAMIENTO")
    print("=" * 70)
    
    plots = [
        'results.png',
        'confusion_matrix.png',
        'F1_curve.png',
        'PR_curve.png',
        'P_curve.png',
        'R_curve.png',
    ]
    
    found_plots = []
    missing_plots = []
    
    for plot_file in plots:
        plot_path = plots_path / plot_file
        if plot_path.exists():
            file_size = plot_path.stat().st_size / 1024  # KB
            found_plots.append(plot_file)
            print(f"✅ {plot_file:25} ({file_size:.1f} KB)")
        else:
            missing_plots.append(plot_file)
    
    if missing_plots:
        print(f"\n⚠️  Gráficas faltantes: {', '.join(missing_plots)}")
    
    print()
    return found_plots

def generate_resume_instructions(metrics, found_files):
    """Generar instrucciones para continuar entrenamiento."""
    print("=" * 70)
    print("🚀 INSTRUCCIONES PARA CONTINUAR ENTRENAMIENTO")
    print("=" * 70)
    
    if not found_files:
        print("❌ No se pueden generar instrucciones: archivos de modelo faltantes")
        print()
        return
    
    if 'last.pt' not in found_files:
        print("⚠️  ADVERTENCIA: last.pt no encontrado")
        print("   Usaremos best.pt, pero el entrenamiento puede reiniciar epochs")
        model_file = 'best.pt'
    else:
        model_file = 'last.pt'
    
    print(f"\n📝 Pasos a seguir:")
    print(f"\n1. Abrir Google Colab:")
    print(f"   https://colab.research.google.com")
    
    print(f"\n2. Subir notebook:")
    print(f"   ml/notebooks/SIRCCD_Training_v3_FromScratch.ipynb")
    
    print(f"\n3. Configurar GPU:")
    print(f"   Runtime → Change runtime type → GPU (T4)")
    
    print(f"\n4. Ejecutar código:")
    print(f"   ```python")
    print(f"   from ultralytics import YOLO")
    print(f"   model = YOLO('/content/drive/MyDrive/SIRCCD_Models/train/weights/{model_file}')")
    print(f"   model.train(")
    print(f"       data='/content/sirccd_dataset/data.yaml',")
    print(f"       epochs=100,")
    print(f"       resume=True,  # ⚠️ IMPORTANTE")
    print(f"       project='/content/drive/MyDrive/SIRCCD_Models',")
    print(f"       name='train',")
    print(f"       exist_ok=True")
    print(f"   )")
    print(f"   ```")
    
    if metrics:
        remaining_epochs = metrics['total_epochs'] - metrics['epoch']
        hours_per_epoch = 3.5 / 60  # ~3.5 min por epoch en T4
        estimated_hours = remaining_epochs * hours_per_epoch
        
        print(f"\n⏱️  Tiempo estimado:")
        print(f"   - Epochs restantes: {remaining_epochs}")
        print(f"   - Tiempo por epoch: ~3.5 min (GPU T4)")
        print(f"   - Tiempo total: ~{estimated_hours:.1f} horas")
    
    print(f"\n📚 Referencias:")
    print(f"   - Guía completa: ml/docs/GUIA_CONTINUAR_ENTRENAMIENTO.md")
    print(f"   - Documentación YOLOv8: https://docs.ultralytics.com/")
    
    print()

def check_drive_space(drive_path):
    """Verificar espacio disponible en Drive."""
    print("=" * 70)
    print("💾 ESPACIO EN DRIVE")
    print("=" * 70)
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(drive_path)
        
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)
        used_pct = (used / total) * 100
        
        print(f"Total:      {total_gb:.2f} GB")
        print(f"Usado:      {used_gb:.2f} GB ({used_pct:.1f}%)")
        print(f"Disponible: {free_gb:.2f} GB")
        
        # Advertencias
        if free_gb < 10:
            print(f"\n⚠️  ADVERTENCIA: Poco espacio disponible (<10 GB)")
            print(f"   Recomendado liberar espacio antes de continuar")
        elif free_gb < 20:
            print(f"\n⚠️  Espacio ajustado (~{free_gb:.1f} GB disponibles)")
            print(f"   Monitorear durante entrenamiento")
        else:
            print(f"\n✅ Espacio suficiente para continuar entrenamiento")
        
        print()
        
    except Exception as e:
        print(f"⚠️  No se pudo verificar espacio: {e}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description='Verificar estado de entrenamiento guardado en Google Drive'
    )
    parser.add_argument(
        '--drive-path',
        type=str,
        required=True,
        help='Ruta a la carpeta de Google Drive montada (ej: /content/drive/MyDrive o C:/Users/usuario/Google Drive)'
    )
    
    args = parser.parse_args()
    
    drive_path = Path(args.drive_path)
    
    if not drive_path.exists():
        print(f"❌ ERROR: Ruta no encontrada: {drive_path}")
        print(f"\nVerifica que Google Drive esté montado/sincronizado")
        print(f"\nRutas comunes:")
        print(f"  - Colab:   /content/drive/MyDrive")
        print(f"  - Windows: C:/Users/[usuario]/Google Drive")
        print(f"  - macOS:   /Users/[usuario]/Google Drive")
        print(f"  - Linux:   ~/Google Drive")
        sys.exit(1)
    
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SIRCCD - Verificación de Entrenamiento" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Verificaciones
    found_files, missing_files = check_model_files(drive_path)
    dataset_ok = check_dataset(drive_path)
    metrics = parse_results_csv(drive_path)
    plots = analyze_training_plots(drive_path)
    check_drive_space(drive_path)
    generate_resume_instructions(metrics, found_files)
    
    # Resumen final
    print("=" * 70)
    print("📋 RESUMEN")
    print("=" * 70)
    
    checks = {
        'Modelos encontrados': len(found_files) >= 1,
        'Dataset disponible': dataset_ok,
        'Métricas analizadas': metrics is not None,
        'Gráficas generadas': len(plots) >= 3,
    }
    
    all_ok = all(checks.values())
    
    for check_name, check_result in checks.items():
        icon = "✅" if check_result else "❌"
        print(f"{icon} {check_name}")
    
    print()
    
    if all_ok:
        print("🎉 Todo listo para continuar entrenamiento")
    elif len(found_files) >= 1 and dataset_ok:
        print("⚠️  Puedes continuar, pero revisa las advertencias arriba")
    else:
        print("❌ Faltan archivos críticos, verifica tu Google Drive")
    
    print("=" * 70)
    print()

if __name__ == '__main__':
    main()
