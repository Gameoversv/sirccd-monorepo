# ⚠️ PROBLEMA DE COMPATIBILIDAD: Python 3.14 Alpha + PyTorch

## Problema

Python 3.14.0a7 (alpha) introdujo cambios en el sistema de anotaciones de tipos que causan incompatibilidad con PyTorch 2.9.x y 2.10.x.

### Error Específico

```
TypeError: OpOverloadPacket.__annotate__() takes 1 positional argument but 2 were given
```

Este error ocurre en `torch/_meta_registrations.py` al intentar importar PyTorch.

## Estado de Dependencias

### ✅ Instaladas Correctamente
- Jupyter (notebook 7.5.3)
- TensorBoard (2.20.0)
- Albumentations
- Pandas
- NumPy 1.26.4 (downgrade desde 2.4.2)
- psycopg2-binary (2.9.11)
- PyYAML (6.0.3)
- python-dotenv
- MinIO (7.2.20)
- FAISS-CPU
- Annoy
- GeoPandas

### ❌ No Funcionales
- PyTorch 2.9.1 / 2.10.0 (error de anotaciones)
- TorchVision 0.24.1 / 0.25.0 (depende de PyTorch)
- Torchaudio 2.9.1 / 2.10.0 (depende de PyTorch)
- Ultralytics (depende de PyTorch)

## Soluciones

### Opción 1: Downgrade a Python 3.12 (RECOMENDADO) ✅

Python 3.12 es estable y totalmente compatible con PyTorch.

#### Pasos:

1. **Descargar Python 3.12.x**
   - [Python 3.12.0](https://www.python.org/downloads/release/python-3120/)
   - Versión recomendada: Python 3.12.7 (última estable)

2. **Crear nuevo entorno virtual**
   ```bash
   # Desde el directorio raíz del monorepo
   cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo
   
   # Renombrar entorno actual como backup
   Rename-Item .venv .venv-py314-backup
   
   # Crear nuevo entorno con Python 3.12
   py -3.12 -m venv .venv
   
   # Activar entorno
   .\.venv\Scripts\Activate.ps1
   
   # Actualizar pip
   python -m pip install --upgrade pip
   
   # Instalar dependencias
   pip install -r ml/requirements-training.txt
   ```

3. **Verificar instalación**
   ```bash
   python ml/scripts/verify_environment.py
   ```

### Opción 2: Usar PyTorch Nightly Build (EXPERIMENTAL) ⚠️

PyTorch nightly puede tener soporte preliminar para Python 3.14, pero es inestable.

```bash
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
```

**Riesgos**:
- Builds inestables
- APIs pueden cambiar
- No recomendado para producción

### Opción 3: Esperar a PyTorch 2.6+ ⏳

PyTorch eventualmente agregará soporte para Python 3.14 cuando esté estable.

**Timeline estimado**:
- Python 3.14 stable: Octubre 2026
- PyTorch con soporte 3.14: Noviembre-Diciembre 2026

## Recomendación Final

**Usar Python 3.12.7** para entrenamiento de modelos:

### Ventajas
- ✅ Totalmente compatible con PyTorch
- ✅ Versión estable y probada
- ✅ Mejor rendimiento que alpha
- ✅ Soporte completo de librerías ML
- ✅ Sin bugs de versión alpha

### Versiones Probadas que Funcionan
- **Python 3.11.x** + PyTorch 2.1.0+
- **Python 3.12.x** + PyTorch 2.1.0+ ⭐ RECOMENDADO
- **Python 3.13.x** + PyTorch 2.5.0+ (experimental)

## Para Continuar con Python 3.14 (No ML)

Si deseas mantener Python 3.14 para otras partes del proyecto (backend, frontend), puedes:

1. **Usar entornos separados**
   ```
   sirccd-monorepo/
   ├── .venv-py314/        # Para backend/otros
   └── .venv-ml-py312/     # Para ML
   ```

2. **Configurar IDE para usar entorno ML**
   - VS Code: `.vscode/settings.json`
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv-ml-py312/Scripts/python.exe"
   }
   ```

## Estado Actual del Proyecto M-01

### ✅ Completado
- Estructura de directorios
- Archivo requirements-training.txt
- Scripts de verificación
- Documentación (M-01_ENVIRONMENT_SETUP.md)
- Notebooks de exploración
- Configuración de variables (.env)
- Instalación de dependencias no-PyTorch

### ⏸️ Bloqueado
- Verificación completa de entorno (requiere PyTorch)
- Kernel de Jupyter configurado (requiere Python estable)
- Entrenamiento de modelos (requiere PyTorch)

## Próximos Pasos

1. **Downgrade a Python 3.12** siguiendo Opción 1
2. **Reinstalar dependencias**
3. **Ejecutar verify_environment.py** para confirmar
4. **Configurar Jupyter kernel**
5. **Proceder con M-02**: Entrenamiento Baseline

## Referencias

- [PyTorch Installation](https://pytorch.org/get-started/locally/)
- [Python 3.14 What's New](https://docs.python.org/3.14/whatsnew/3.14.html)
- [PEP 649 - Deferred Evaluation Of Annotations](https://peps.python.org/pep-0649/)
- [PyTorch GitHub Issue Tracker](https://github.com/pytorch/pytorch/issues)

## Contacto

Si encuentras una solución alternativa o PyTorch agrega soporte para Python 3.14, actualiza este documento.

---

**Fecha**: 17 de febrero de 2026  
**Versión Python**: 3.14.0a7 (alpha 7)  
**Versión PyTorch probadas**: 2.9.1, 2.10.0  
**Estado**: Incompatible
