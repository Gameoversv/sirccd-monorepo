#!/usr/bin/env python3
"""
Script de inicio rápido para SIRCCD Backend
"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Verificar versión de Python"""
    if sys.version_info < (3, 11):
        print("❌ Se requiere Python 3.11 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_venv():
    """Verificar si está en un entorno virtual"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        print("⚠️  No se detectó un entorno virtual")
print("   Recomendado: python -m venv .venv y activar el entorno")
        return False
    print("✅ Entorno virtual activo")
    return True


def check_env_file():
    """Verificar archivo .env"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        print("   Copiando desde .env.example...")
        example = Path(".env.example")
        if example.exists():
            import shutil
            shutil.copy(example, env_file)
            print("✅ Archivo .env creado")
            print("   📝 Revisa y edita .env con tus configuraciones")
        else:
            print("❌ No se encontró .env.example")
            return False
    else:
        print("✅ Archivo .env encontrado")
    return True


def install_dependencies():
    """Instalar dependencias"""
    print("\n📦 Instalando dependencias...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✅ Dependencias instaladas")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error instalando dependencias")
        return False


def start_server():
    """Iniciar servidor"""
    print("\n🚀 Iniciando servidor FastAPI...")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/api/v1/docs")
    print("\n   Presiona Ctrl+C para detener\n")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido")


def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 SIRCCD Backend - Inicio Rápido")
    print("=" * 60)
    print()
    
    # Verificaciones
    if not check_python_version():
        sys.exit(1)
    
    check_venv()  # Warning pero no bloquea
    
    if not check_env_file():
        sys.exit(1)
    
    # Preguntar si instalar dependencias
    response = input("\n¿Instalar/actualizar dependencias? (s/n): ")
    if response.lower() in ['s', 'y', 'yes', 'si', 'sí']:
        if not install_dependencies():
            sys.exit(1)
    
    # Iniciar servidor
    start_server()


if __name__ == "__main__":
    main()
