# Image de l'API FastAPI, en deux étapes :
#   1. builder : uv installe les dépendances (groupe « api » seulement) dans /app/.venv
#   2. runtime : image Python légère, utilisateur non root, on copie le venv et le code
#
# Construire :  docker build -f docker/api.Dockerfile -t diabetes-api .
# Lancer :      docker run --rm -p 8000:8000 diabetes-api
# Prérequis :   le modèle doit exister (uv run dvc repro) : il est copié dans l'image.

FROM ghcr.io/astral-sh/uv:0.9.17-python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# 1) Dépendances seules : cette couche est mise en cache tant que pyproject/uv.lock ne changent pas
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group api

# 2) Code du projet, installé dans le venv (non éditable)
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable --no-default-groups --group api

# 3) Modèle entraîné (models/model.joblib + model_info.json)
COPY models ./models


FROM python:3.11-slim-bookworm AS runtime
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/models /app/models
COPY --chown=appuser:appuser api ./api

ENV PATH="/app/.venv/bin:$PATH" \
    MODEL_PATH=/app/models/model.joblib \
    PORT=8000 \
    PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT','8000') + '/health').status == 200 else 1)"
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
