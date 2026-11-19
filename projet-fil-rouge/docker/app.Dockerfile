# Image de l'application Streamlit (groupe « app »).
# En mode API (API_URL défini) elle n'a pas besoin du modèle ; en mode local elle
# utilise models/model.joblib s'il est présent, sinon s'entraîne au démarrage à
# partir de data/raw/diabetes.csv (repli de démonstration).
#
# Construire :  docker build -f docker/app.Dockerfile -t diabetes-app .
# Lancer :      docker run --rm -p 8501:8501 -e API_URL=http://host.docker.internal:8000 diabetes-app

FROM ghcr.io/astral-sh/uv:0.9.17-python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group app
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable --no-default-groups --group app
COPY models ./models


FROM python:3.11-slim-bookworm AS runtime
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/models /app/models
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser data/raw ./data/raw
COPY --chown=appuser:appuser src ./src

ENV PATH="/app/.venv/bin:$PATH" \
    MODEL_PATH=/app/models/model.joblib \
    PORT=8501 \
    PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health').status == 200 else 1)"
CMD ["sh", "-c", "streamlit run app/streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true"]
