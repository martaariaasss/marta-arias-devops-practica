# syntax=docker/dockerfile:1
# =============================================================================
# Dockerfile — Tienda Online API (FastAPI)
# Autora: Marta Arias
#
# Build multi-stage:
#   1) builder -> instala las dependencias en un entorno virtual aislado (/opt/venv)
#   2) runtime -> imagen final mínima: solo Python, el venv y el código fuente
# Así la imagen final no contiene caché de pip ni herramientas de instalación.
# =============================================================================

# (1a) Imagen base oficial y ligera
ARG PYTHON_IMAGE=python:3.12-slim

# -----------------------------------------------------------------------------
# Etapa 1: builder — instalación de dependencias
# -----------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# (1b) Se copia SOLO requirements.txt antes que el código: mientras las dependencias
#      no cambien, Docker reutiliza esta capa en caché y los builds son mucho más rápidos.
COPY requirements.txt /tmp/requirements.txt

# (1c) Instalación de las dependencias (versiones fijadas) sin guardar caché
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# Etapa 2: runtime — imagen final
# -----------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime

ARG APP_VERSION=1.0.0

# Metadatos estándar OCI
LABEL org.opencontainers.image.title="tienda-online-api" \
      org.opencontainers.image.description="Tienda online: API REST con FastAPI y TiendaService + frontend web en /tienda" \
      org.opencontainers.image.authors="Marta Arias" \
      org.opencontainers.image.version="${APP_VERSION}"

# - PYTHONDONTWRITEBYTECODE: no genera .pyc (el código es de solo lectura)
# - PYTHONUNBUFFERED: los logs salen al instante por stdout (docker logs)
# - HOST=0.0.0.0: escucha en todas las interfaces para que el puerto publicado funcione
# - CARGAR_DATOS_EJEMPLO: carga al arrancar los usuarios y productos de la Práctica 1
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=info \
    CARGAR_DATOS_EJEMPLO=true \
    APP_VERSION=${APP_VERSION}

# Usuario y grupo de sistema sin privilegios (el contenedor NO se ejecuta como root)
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Dependencias ya instaladas en la etapa builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# (1d) Copia del código fuente (API + frontend de la tienda en src/frontend)
COPY src/ ./src/

# (1e) Permisos: el código pertenece a root y el grupo "app" puede leerlo y
#      ejecutarlo, pero no modificarlo (si alguien comprometiera la app,
#      no podría alterar su propio código). "X" da ejecución solo a carpetas.
RUN chown -R root:app /app \
 && chmod -R u=rwX,g=rX,o= /app

USER app
WORKDIR /app/src

EXPOSE 8000

# Docker comprueba periódicamente que la API responde (estado "healthy")
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=2)" || exit 1

# (1f) Comando de inicio: el main ejecutable de la aplicación (forma exec,
#      para que la app reciba directamente las señales de parada de Docker)
CMD ["python", "main.py"]
