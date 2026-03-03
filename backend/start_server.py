"""
Script para iniciar el servidor FastAPI con recarga automática
"""
import subprocess
import sys
from pathlib import Path

# Obtener el path correcto
backend_dir = Path(__file__).parent

print("=" * 60)
print("🚀 INICIANDO SERVIDOR SIRCCD")
print("=" * 60)
print(f"\n📂 Directorio: {backend_dir}")
print(f"🌐 URL: http://localhost:8000")
print(f"📚 Swagger UI: http://localhost:8000/docs")
print(f"📖 ReDoc: http://localhost:8000/redoc")
print(f"\n⏹️  Detener: Ctrl+C")
print("=" * 60 + "\n")

# Iniciar servidor con uvicorn
try:
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ], cwd=backend_dir)
except KeyboardInterrupt:
    print("\n\n✅ Servidor detenido")
