# Lab 6 · Emballer l'application avec Docker

**Durée** : 40 min · **Objectif** : une image Docker pour l'API, une pour l'interface, et `docker compose up` qui lance les deux ensemble.

Référence : [projet-fil-rouge/docker](../../projet-fil-rouge/docker) et [docker-compose.yml](../../projet-fil-rouge/docker-compose.yml). Docker Desktop doit être démarré.

## ★ Parcours de base

### 1. Un premier conteneur, sans rien écrire

```bash
docker run --rm -p 8080:80 nginx:alpine
```

Ouvrez http://localhost:8080 : un serveur web tourne dans un conteneur. `Ctrl+C` l'arrête, `--rm` le supprime. Vous venez de lancer une image publique ; nous allons construire la nôtre.

### 2. Le Dockerfile de l'API

Créez `docker/api.Dockerfile` :

```dockerfile
FROM ghcr.io/astral-sh/uv:0.9.17-python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group api
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable --no-default-groups --group api
COPY models ./models

FROM python:3.11-slim-bookworm
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/models /app/models
COPY --chown=appuser:appuser api ./api
ENV PATH="/app/.venv/bin:$PATH" MODEL_PATH=/app/models/model.joblib PORT=8000
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
```

Si votre `pyproject.toml` n'a pas de groupe `api`, remplacez `--no-default-groups --group api` par `--no-dev`.

Créez `.dockerignore` :

```
.venv
.git
__pycache__
*.pyc
mlruns
mlflow.db
data/processed
tests
.env
```

### 3. Construire et lancer

```bash
uv run dvc repro                                            # le modèle doit exister
docker build -f docker/api.Dockerfile -t diabete-api .
docker image ls diabete-api                                 # quelle taille ?
docker run --rm -p 8000:8000 diabete-api
```

Dans un autre terminal : http://localhost:8000/docs fonctionne, servi depuis le conteneur. Puis :

```bash
docker ps                          # le conteneur et son identifiant
docker logs <id>                   # les journaux d'uvicorn
docker exec -it <id> sh            # un shell dedans : ls, env, whoami
```

Question : que renvoie `whoami` dans le conteneur ? Pourquoi est-ce important ?

### 4. Le cache de couches

Modifiez un commentaire dans `api/main.py` et reconstruisez : `docker build` ne réinstalle pas les dépendances (les couches `uv sync` sont « CACHED »). Modifiez maintenant `pyproject.toml` (ajoutez une dépendance) : tout se réinstalle. C'est l'effet de l'ordre des instructions `COPY`.

### 5. Docker Compose

Créez `docker-compose.yml` à la racine :

```yaml
services:
  api:
    build: { context: ., dockerfile: docker/api.Dockerfile }
    ports: ["8000:8000"]
  app:
    build: { context: ., dockerfile: docker/app.Dockerfile }
    ports: ["8501:8501"]
    environment:
      API_URL: http://api:8000
    depends_on: [api]
```

Et `docker/app.Dockerfile` sur le même modèle que l'API (groupe `app`, copie de `app/` et `src/`, commande `streamlit run app/streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0`, port 8501). Le fil rouge en contient une version complète.

```bash
docker compose up --build
```

Ouvrez http://localhost:8501 : l'interface, en mode API, parle à `http://api:8000`. Ce nom n'existe que dans le réseau Compose : c'est le DNS interne.

```bash
docker compose ps
docker compose logs -f api
docker compose down
```

## ★★ Aller plus loin

- **Sonde de santé** : `HEALTHCHECK` dans le Dockerfile (voir le fil rouge), puis `depends_on: { api: { condition: service_healthy } }` dans Compose.
- **Un troisième service** : le serveur MLflow (`ghcr.io/mlflow/mlflow:v3.1.0`) avec un volume ; envoyez-y vos runs avec `MLFLOW_TRACKING_URI=http://localhost:5000`.
- **Taille** : comparez l'image en une étape (tout dans `builder`) et en deux étapes. Essayez `docker history diabete-api`.
- **Variables d'environnement** : `docker run -e THRESHOLD=0.3 …` et vérifiez que l'API change de seuil sans reconstruire l'image.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `error during connect` | Docker Desktop n'est pas démarré | le lancer, attendre l'icône verte |
| `COPY models: not found` | pas de modèle entraîné | `uv run dvc repro` avant `docker build` |
| `uv sync --frozen` échoue | `uv.lock` pas à jour | `uv lock` en local, puis commit |
| L'interface ne joint pas l'API | `API_URL=http://localhost:8000` au lieu de `http://api:8000` | dans Compose, utiliser le nom du service |
| Port déjà alloué | un conteneur précédent tourne encore | `docker ps`, `docker stop <id>` |

## Ce qu'il faut retenir

Une image = un environnement complet et figé ; deux étapes pour une image petite ; Compose pour décrire plusieurs services et leur réseau. Solution complète : publiée après la séance.
