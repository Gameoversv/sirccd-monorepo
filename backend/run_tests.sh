#!/bin/bash
# Script para ejecutar suite completa de tests del backend SIRCCD

set -e  # Detener en caso de error

echo "======================================"
echo "🧪 SIRCCD Backend Test Suite (B-11)"
echo "======================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "📦 Activando entorno virtual..."
    source .venv/bin/activate
fi

# Verificar que pytest esté instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest no está instalado${NC}"
    echo "Instalando dependencias..."
    pip install -r requirements.txt
fi

# Parse argumentos
TEST_TYPE="${1:-all}"

case $TEST_TYPE in
    "unit")
        echo -e "${YELLOW}🧪 Ejecutando tests unitarios...${NC}"
        pytest -m unit -v --cov --cov-report=term-missing
        ;;
    
    "integration")
        echo -e "${YELLOW}🔗 Ejecutando tests de integración...${NC}"
        pytest -m integration -v --cov --cov-report=term-missing
        ;;
    
    "contract")
        echo -e "${YELLOW}📄 Ejecutando tests de contrato...${NC}"
        pytest -m contract -v
        ;;
    
    "auth")
        echo -e "${YELLOW}🔐 Ejecutando tests de autenticación...${NC}"
        pytest tests/test_auth.py -v --cov --cov-report=term-missing
        ;;
    
    "reports")
        echo -e "${YELLOW}📝 Ejecutando tests de reportes...${NC}"
        pytest tests/test_reports.py -v --cov --cov-report=term-missing
        ;;
    
    "incidents")
        echo -e "${YELLOW}🚨 Ejecutando tests de incidentes...${NC}"
        pytest tests/test_incidents.py -v --cov --cov-report=term-missing
        ;;
    
    "fast")
        echo -e "${YELLOW}⚡ Ejecutando tests rápidos (sin slow)...${NC}"
        pytest -m "not slow" -v --cov --cov-report=term-missing
        ;;
    
    "coverage")
        echo -e "${YELLOW}📊 Ejecutando tests con coverage completo...${NC}"
        pytest --cov --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}✅ Reporte HTML generado en: htmlcov/index.html${NC}"
        # Abrir en navegador (Linux)
        if command -v xdg-open &> /dev/null; then
            xdg-open htmlcov/index.html
        fi
        ;;
    
    "all"|*)
        echo -e "${YELLOW}🧪 Ejecutando TODOS los tests...${NC}"
        echo ""
        
        echo "1️⃣  Tests Unitarios"
        pytest -m unit --cov --cov-report=term-missing
        echo ""
        
        echo "2️⃣  Tests de Integración"
        pytest -m integration --cov --cov-append --cov-report=term-missing
        echo ""
        
        echo "3️⃣  Tests de Contrato"
        pytest -m contract -v
        echo ""
        
        echo "4️⃣  Generando reporte HTML..."
        pytest --cov --cov-report=html > /dev/null 2>&1
        echo ""
        ;;
esac

# Mostrar resumen
echo ""
echo "======================================"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tests completados exitosamente!${NC}"
else
    echo -e "${RED}❌ Algunos tests fallaron${NC}"
    exit 1
fi
echo "======================================"

# Mostrar comandos disponibles si no se pasó argumento
if [ "$TEST_TYPE" == "all" ] || [ -z "$1" ]; then
    echo ""
    echo "💡 Comandos disponibles:"
    echo "   ./run_tests.sh unit         - Solo tests unitarios"
    echo "   ./run_tests.sh integration  - Solo tests de integración"
    echo "   ./run_tests.sh contract     - Solo tests de contrato"
    echo "   ./run_tests.sh auth         - Tests de autenticación"
    echo "   ./run_tests.sh reports      - Tests de reportes"
    echo "   ./run_tests.sh incidents    - Tests de incidentes"
    echo "   ./run_tests.sh fast         - Tests rápidos (sin slow)"
    echo "   ./run_tests.sh coverage     - Tests con reporte HTML"
    echo ""
fi
