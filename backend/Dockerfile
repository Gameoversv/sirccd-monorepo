FROM python:3.11-slim

LABEL maintainer="SIRCCD Team"
LABEL description="SIRCCD Backend - FastAPI Application"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema (libpq para postgres, libgeos para geoalchemy2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libgeos-dev \
    libspatialindex-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .

# torch/torchvision desde el indice CPU: el wheel por defecto arrastra las
# librerias CUDA (~2.5 GB) que no se usan en este despliegue.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch>=2.2.0" "torchvision>=0.17.0"

RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Directorios de trabajo
RUN mkdir -p logs uploads storage

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Shell form: la plataforma inyecta PORT en runtime y hay que expandirlo.
# forwarded-allow-ips: el proxy TLS de Railway no es 127.0.0.1 (el default de
# uvicorn), asi que sin esto descarta su X-Forwarded-Proto, cree servir http y
# emite los redirects absolutos (307 de barra final) apuntando a http://. El
# navegador los bloquea como mixed content. El contenedor solo es alcanzable a
# traves del proxy, asi que confiar en la cabecera es seguro aqui.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips="*"
