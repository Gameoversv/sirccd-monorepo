# Scripts de inicio rápido para SIRCCD Backend

## start.sh (Linux/Mac)
#!/bin/bash

echo "🚀 SIRCCD Backend - Inicio Rápido"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado"
    exit 1
fi

# Activar entorno virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️  Creando entorno virtual..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Verificar .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Archivo .env creado desde .env.example"
        echo "📝 Edita .env con tus configuraciones"
    fi
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Iniciar servidor
echo ""
echo "🚀 Iniciando servidor..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/api/v1/docs"
echo ""
python main.py
