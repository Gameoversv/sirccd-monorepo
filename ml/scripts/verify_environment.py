"""
Script de verificación de entorno ML - SIRCCD
M-01: Preparación de entorno de entrenamiento

Verifica que todas las dependencias estén correctamente instaladas.
"""

import sys
import importlib
from pathlib import Path


def check_package(package_name, import_name=None, min_version=None):
    """
    Verifica si un paquete está instalado.
    
    Args:
        package_name: Nombre del paquete para mostrar
        import_name: Nombre para importación (si es diferente)
        min_version: Versión mínima requerida (opcional)
    
    Returns:
        bool: True si está instalado, False si no
    """
    if import_name is None:
        import_name = package_name
    
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, '__version__', 'unknown')
        
        status = "✅"
        version_info = version
        
        # Verificar versión mínima si se especifica
        if min_version and version != 'unknown':
            try:
                from packaging import version as pkg_version
                if pkg_version.parse(version) < pkg_version.parse(min_version):
                    status = "⚠️"
                    version_info = f"{version} (required: >={min_version})"
            except:
                pass
        
        print(f"{status} {package_name:<25} {version_info}")
        return True
    except ImportError:
        print(f"❌ {package_name:<25} NOT INSTALLED")
        return False


def check_cuda():
    """Verifica disponibilidad de CUDA."""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.version.cuda}")
            print(f"   GPU device: {torch.cuda.get_device_name(0)}")
            print(f"   GPU count: {torch.cuda.device_count()}")
        else:
            print("⚠️  CUDA not available (CPU only)")
        return torch.cuda.is_available()
    except:
        print("❌ Cannot check CUDA (torch not installed)")
        return False


def check_directories():
    """Verifica que existan los directorios necesarios."""
    base_dir = Path(__file__).parent.parent  # ml/
    
    required_dirs = [
        'datasets',
        'notebooks',
        'models',
        'runs',
        'scripts',
        'configs',
        'docs'
    ]
    
    print("\n📁 Directorios:")
    all_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (creating...)")
            dir_path.mkdir(parents=True, exist_ok=True)
            all_exist = False
    
    return all_exist


def check_jupyter_kernel():
    """Verifica si el kernel de Jupyter está instalado."""
    try:
        import subprocess
        result = subprocess.run(
            ['jupyter', 'kernelspec', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'sirccd-ml' in result.stdout:
            print("✅ Jupyter kernel 'sirccd-ml' instalado")
            return True
        else:
            print("⚠️  Jupyter kernel 'sirccd-ml' no encontrado")
            print("   Ejecutar: python -m ipykernel install --user --name=sirccd-ml --display-name=\"SIRCCD ML\"")
            return False
    except Exception as e:
        print(f"❌ Error verificando kernel: {e}")
        return False


def main():
    print("=" * 70)
    print(" " * 15 + "VERIFICACIÓN DE ENTORNO ML - SIRCCD")
    print("=" * 70)
    
    print(f"\n🐍 Python: {sys.version}")
    print(f"   Executable: {sys.executable}")
    
    # Verificar dependencias core
    print("\n" + "=" * 70)
    print("📦 DEPENDENCIAS CORE")
    print("=" * 70)
    
    core_packages = [
        ('PyTorch', 'torch', '2.1.0'),
        ('TorchVision', 'torchvision', '0.16.0'),
        ('Ultralytics', 'ultralytics', '8.0.0'),
    ]
    
    core_ok = all(check_package(name, imp, ver) for name, imp, ver in core_packages)
    
    # Verificar procesamiento de imágenes
    print("\n" + "=" * 70)
    print("🖼️  PROCESAMIENTO DE IMÁGENES")
    print("=" * 70)
    
    image_packages = [
        ('OpenCV', 'cv2', '4.8.0'),
        ('Pillow', 'PIL', '10.0.0'),
        ('Albumentations', 'albumentations', '1.3.0'),
        ('scikit-image', 'skimage', '0.21.0'),
    ]
    
    image_ok = all(check_package(name, imp, ver) for name, imp, ver in image_packages)
    
    # Verificar data science
    print("\n" + "=" * 70)
    print("📊 DATA SCIENCE")
    print("=" * 70)
    
    ds_packages = [
        ('NumPy', 'numpy', '1.24.0'),
        ('Pandas', 'pandas', '2.0.0'),
        ('Matplotlib', 'matplotlib', '3.7.0'),
        ('Seaborn', 'seaborn', '0.12.0'),
    ]
    
    ds_ok = all(check_package(name, imp, ver) for name, imp, ver in ds_packages)
    
    # Verificar Jupyter
    print("\n" + "=" * 70)
    print("📓 JUPYTER")
    print("=" * 70)
    
    jupyter_packages = [
        ('Jupyter', 'jupyter', '1.0.0'),
        ('Notebook', 'notebook', '7.0.0'),
        ('IPyKernel', 'ipykernel', '6.25.0'),
        ('IPyWidgets', 'ipywidgets', '8.1.0'),
    ]
    
    jupyter_ok = all(check_package(name, imp, ver) for name, imp, ver in jupyter_packages)
    
    # Verificar experiment tracking
    print("\n" + "=" * 70)
    print("📈 EXPERIMENT TRACKING")
    print("=" * 70)
    
    tracking_packages = [
        ('TensorBoard', 'tensorboard', '2.14.0'),
        ('Weights & Biases', 'wandb', '0.16.0'),
    ]
    
    tracking_ok = all(check_package(name, imp, ver) for name, imp, ver in tracking_packages)
    
    # Verificar vector search
    print("\n" + "=" * 70)
    print("🔍 VECTOR SIMILARITY SEARCH")
    print("=" * 70)
    
    vector_packages = [
        ('FAISS', 'faiss', '1.7.4'),
        ('Annoy', 'annoy', '1.17.0'),
    ]
    
    vector_ok = all(check_package(name, imp) for name, imp, _ in vector_packages)
    
    # Verificar GIS
    print("\n" + "=" * 70)
    print("🗺️  GIS y GEOSPATIAL")
    print("=" * 70)
    
    gis_packages = [
        ('GeoPandas', 'geopandas', '0.14.0'),
        ('Shapely', 'shapely', '2.0.0'),
        ('GeoJSON', 'geojson', '3.0.0'),
    ]
    
    gis_ok = all(check_package(name, imp, ver) for name, imp, ver in gis_packages)
    
    # Verificar database
    print("\n" + "=" * 70)
    print("🗄️  DATABASE")
    print("=" * 70)
    
    db_packages = [
        ('psycopg2', 'psycopg2', '2.9.0'),
    ]
    
    db_ok = all(check_package(name, imp, ver) for name, imp, ver in db_packages)
    
    # Verificar utilidades
    print("\n" + "=" * 70)
    print("🔧 UTILIDADES")
    print("=" * 70)
    
    util_packages = [
        ('tqdm', 'tqdm', '4.65.0'),
        ('PyYAML', 'yaml', '6.0.0'),
        ('python-dotenv', 'dotenv', '1.0.0'),
        ('MinIO', 'minio', '7.2.0'),
        ('piexif', 'piexif', '1.1.3'),
    ]
    
    util_ok = all(check_package(name, imp, ver) for name, imp, ver in util_packages)
    
    # Verificar CUDA
    print("\n" + "=" * 70)
    print("🚀 GPU / CUDA")
    print("=" * 70)
    cuda_ok = check_cuda()
    
    # Verificar directorios
    print("\n" + "=" * 70)
    print("📁 ESTRUCTURA DE DIRECTORIOS")
    print("=" * 70)
    dirs_ok = check_directories()
    
    # Verificar Jupyter kernel
    print("\n" + "=" * 70)
    print("🎯 JUPYTER KERNEL")
    print("=" * 70)
    kernel_ok = check_jupyter_kernel()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    results = [
        ("Dependencias Core", core_ok),
        ("Procesamiento de Imágenes", image_ok),
        ("Data Science", ds_ok),
        ("Jupyter", jupyter_ok),
        ("Experiment Tracking", tracking_ok),
        ("Vector Search", vector_ok),
        ("GIS", gis_ok),
        ("Database", db_ok),
        ("Utilidades", util_ok),
        ("Directorios", dirs_ok),
        ("Jupyter Kernel", kernel_ok),
    ]
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    all_ok = all(status for _, status in results)
    
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ ENTORNO COMPLETAMENTE CONFIGURADO")
    else:
        print("⚠️  ENTORNO PARCIALMENTE CONFIGURADO")
        print("   Revisa los elementos marcados con ❌ arriba")
    print("=" * 70)
    
    if cuda_ok:
        print("\n💡 GPU disponible - Entrenamiento acelerado habilitado")
    else:
        print("\n⚠️  GPU no disponible - Entrenamiento será en CPU (más lento)")
    
    return all_ok


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
