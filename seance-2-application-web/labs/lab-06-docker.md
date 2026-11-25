# Lab 6 · Emballer l'application avec Docker

**Durée** : 40 min · **Objectif** : une image Docker pour l'API, une pour l'interface, et `docker compose up` qui lance les deux ensemble.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux. Docker Desktop doit être démarré (icône verte).

**Point de départ** : le projet `diabete-lab` du lab 5, commité, avec un modèle entraîné (`ls models/model.joblib`). Référence : [projet-fil-rouge/docker](../../projet-fil-rouge/docker) et [docker-compose.yml](../../projet-fil-rouge/docker-compose.yml).

## ★ Parcours de base

### 1. Un premier conteneur, sans rien écrire

```bash
docker run --rm -p 8080:80 nginx:alpine
```

Ouvrez http://localhost:8080 : un serveur web tourne dans un conteneur. `Ctrl+C` l'arrête, `--rm` le supprime. Vous venez de lancer une image publique ; vous allez construire la vôtre.

### 2. Le Dockerfile de l'API

Vérifiez votre version de uv avec `uv --version`, puis créez `docker/api.Dockerfile` en mettant cette version dans la première ligne (ici 0.9.17) :

```dockerfile
# Étape 1 : construire l'environnement avec uv
FROM ghcr.io/astral-sh/uv:0.9.17-python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group api
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable --no-default-groups --group api

# Étape 2 : l'image finale, sans uv ni sources
FROM python:3.11-slim-bookworm
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser models ./models
COPY --chown=appuser:appuser api ./api
ENV PATH="/app/.venv/bin:$PATH" MODEL_PATH=/app/models/model.joblib PORT=8000
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
```

`--no-default-groups --group api` : l'image n'installe que le cœur du projet et le groupe `api`, ni DVC, ni MLflow, ni Streamlit.

Créez `.dockerignore` à la racine, pour ne pas envoyer à Docker ce dont l'image n'a pas besoin :

```
.venv
.git
.dvc/cache
__pycache__
*.pyc
data
mlflow.db
mlruns
mlartifacts
tests
.env
```

### 3. Construire et lancer

```bash
docker build -f docker/api.Dockerfile -t diabete-api .
docker image ls diabete-api
docker run --rm -d -p 8000:8000 --name api-test diabete-api
curl http://localhost:8000/health
docker logs api-test
docker exec api-test whoami
docker stop api-test
```

> **Point de contrôle** : l'image pèse environ 700 Mo ; `/health` répond `{"status":"ok"}` depuis le conteneur ; `whoami` répond `appuser`.

Question : pourquoi est-il important que le conteneur ne tourne pas en `root` ?

### 4. Le cache de couches

Modifiez un commentaire dans `api/main.py`, puis reconstruisez : les étapes `uv sync` affichent `CACHED`, la construction prend quelques secondes. Ajoutez maintenant une dépendance (`uv add --group api pydantic-settings`) et reconstruisez : tout se réinstalle. C'est l'effet de l'ordre des instructions `COPY` : les dépendances d'abord, le code ensuite.

### 5. L'image de l'interface

Créez `docker/app.Dockerfile` (mêmes principes, groupe `app`, port 8501) :

```dockerfile
FROM ghcr.io/astral-sh/uv:0.9.17-python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group app
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable --no-default-groups --group app

FROM python:3.11-slim-bookworm
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser src ./src
ENV PATH="/app/.venv/bin:$PATH" PORT=8501
USER appuser
EXPOSE 8501
CMD ["sh", "-c", "streamlit run app/streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true"]
```

En mode API, l'interface n'a pas besoin du modèle : il n'est pas copié.

### 6. Docker Compose

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
      API_URL: http://api:8000      # le nom du service sert de nom de machine
    depends_on: [api]
```

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
docker compose exec -T app python -c "import httpx; print(httpx.get('http://api:8000/health').json())"
```

> **Point de contrôle** : les deux services sont `running` ; l'API répond `ok`, Streamlit répond `ok` ; depuis le conteneur `app`, l'adresse `http://api:8000` fonctionne. Ouvrez http://localhost:8501 : l'estimation affiche `58%` et « Mode API · http://api:8000 ».

`http://api:8000` n'existe que dans le réseau de Compose : depuis votre navigateur, c'est `localhost:8000`.

```bash
docker compose logs api
docker compose down
git add -A
git commit -m "Images Docker et Compose"
```

## ★★ Aller plus loin

- **Sonde de santé** : `HEALTHCHECK` dans `api.Dockerfile` (voir le fil rouge), puis `depends_on: { api: { condition: service_healthy } }` : Compose attend que l'API réponde avant de lancer l'interface.
- **Un troisième service** : le serveur MLflow (`ghcr.io/mlflow/mlflow:v3.1.0`) avec un volume, comme dans le fil rouge.
- **Taille** : `docker history diabete-api` montre le poids de chaque couche. Quelle couche domine, et pourquoi ?
- **Configuration sans reconstruire** : ajoutez la lecture de `THRESHOLD` (★★ du lab 4), puis `docker run -e THRESHOLD=0.6 …` : même image, autre comportement.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `error during connect` | Docker Desktop n'est pas démarré | le lancer et attendre l'icône verte |
| `COPY models: not found` | pas de modèle entraîné | `uv run dvc repro` avant `docker build` |
| `uv sync --frozen` : lock file out of date | `uv.lock` pas à jour | `uv lock` en local, commit, reconstruire |
| `unsupported lock file version` | uv de l'image plus ancien que le vôtre | mettre votre version (`uv --version`) dans le `FROM` |
| `ModuleNotFoundError: mlflow` au démarrage de l'API | `predict.py` importe `train.py` | `predict.py` ne doit importer que `prepare.py` |
| L'interface ne joint pas l'API | `API_URL=http://localhost:8000` dans Compose | dans Compose, utiliser le nom du service : `http://api:8000` |
| `port is already allocated` | un conteneur ou un uvicorn local occupe le port | `docker ps`, `docker stop <nom>`, ou arrêter l'uvicorn du lab 4 |

## À retenir

- **Une image est un environnement complet et figé** : système, Python, bibliothèques, code et modèle ; un conteneur est cette image en cours d'exécution.
- **Deux étapes** : on construit avec uv, on livre une image sans uv ni sources, avec un utilisateur non root.
- **L'ordre des `COPY` fait le cache** : dépendances d'abord, code ensuite ; changer le code ne réinstalle rien.
- **Compose décrit plusieurs services et leur réseau** : chaque service est joignable par son nom.

## Solution

Solution complète : publiée après la séance.
