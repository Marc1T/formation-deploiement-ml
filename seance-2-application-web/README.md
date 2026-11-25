# Séance 2 · Du modèle à une application web

**Durée** : 3 h · **Slides** : [slides.html](slides.html) · **Labs** : [4 FastAPI](labs/lab-04-fastapi.md) · [5 Streamlit](labs/lab-05-streamlit.md) · [6 Docker](labs/lab-06-docker.md) · [7 CI](labs/lab-07-ci.md) · **Mémo** : [toutes les commandes de la séance](memo.md)

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux. **Point de départ** : le projet `diabete-lab` construit pendant la séance 1.

À la fin de la séance, votre modèle répond à des requêtes HTTP, une interface web l'interroge, le tout tourne dans des conteneurs, et chaque `git push` lance automatiquement les tests et construit l'image.

## Déroulé

| Temps | Contenu | Support |
|---|---|---|
| 0:00 – 0:30 | Architecture : modèle, API, interface ; REST, JSON, validation | §1 |
| 0:30 – 1:15 | FastAPI : servir le modèle, documenter, tester | §2, Lab 4 |
| 1:15 – 1:45 | Streamlit : une interface qui appelle l'API | §3, Lab 5 |
| 1:45 – 2:30 | Docker : emballer l'application, Docker Compose | §4, Lab 6 |
| 2:30 – 3:00 | Intégration continue avec GitHub Actions | §5, Lab 7 |

## 1. Architecture : trois briques et deux frontières

![Architecture trois tiers](../assets/diagrams/architecture-3-tiers.svg)

Pourquoi ne pas tout mettre dans une seule application Streamlit qui charge le modèle ? C'est possible (le fil rouge le fait en « mode local »), et c'est suffisant pour une démonstration. Mais séparer l'**API** de l'**interface** apporte trois choses :

1. **Plusieurs clients** : un site web, une application mobile, un script batch utilisent la même API.
2. **Des cycles de vie différents** : on redéploie le modèle sans toucher à l'interface, et inversement.
3. **Des ressources différentes** : l'API a besoin de CPU et de mémoire pour le modèle, l'interface non.

Le contrat entre les deux est une requête HTTP avec du JSON. Voici le trajet d'une prédiction :

![Le trajet d'une prédiction](../assets/diagrams/request-flow.svg)

Vocabulaire minimal :

| Terme | Sens |
|---|---|
| **Endpoint** (route) | Une URL et une méthode : `POST /predict`, `GET /health` |
| **JSON** | Le format d'échange : `{"glucose": 138, "bmi": 33.6}` |
| **Code de statut** | `200` OK, `422` entrée invalide, `503` service indisponible |
| **Schéma** | La description des champs attendus et renvoyés (Pydantic côté Python, OpenAPI côté documentation) |

## 2. FastAPI : servir le modèle

### Pourquoi FastAPI

- Les **schémas Pydantic** valident l'entrée (types, bornes) et documentent la sortie : une requête mal formée reçoit un `422` explicite sans toucher au modèle.
- La **documentation interactive** (`/docs`) est générée automatiquement : vos camarades testent l'API depuis le navigateur.
- C'est **rapide** et **standard** : uvicorn, ASGI, le même modèle que les grands frameworks.

### Le squelette

Extrait de [api/main.py](../projet-fil-rouge/api/main.py) :

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from api.schemas import PatientFeatures, PredictionOut
from diabetes_ml.predict import Predictor

state = {"predictor": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    state["predictor"] = Predictor("models/model.joblib")   # chargé une fois au démarrage
    yield

app = FastAPI(title="API Risque de diabète", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok" if state["predictor"] else "degraded"}

@app.post("/predict", response_model=PredictionOut)
def predict(patient: PatientFeatures):
    if state["predictor"] is None:
        raise HTTPException(503, "Modèle non chargé")
    return state["predictor"].predict_one(patient.model_dump())
```

Trois détails qui comptent en production :

- Le modèle est chargé **une fois** dans `lifespan`, pas à chaque requête.
- `/health` existe dès le premier jour : Docker, Azure et Cloud Run s'en servent pour savoir si l'instance est prête.
- Le `503` dit clairement ce qui ne va pas, au lieu d'une erreur 500 anonyme.

### Le schéma d'entrée

Extrait de [api/schemas.py](../projet-fil-rouge/api/schemas.py) :

```python
from pydantic import BaseModel, Field

class PatientFeatures(BaseModel):
    pregnancies: int = Field(ge=0, le=20, description="Nombre de grossesses")
    glucose: float = Field(ge=0, le=300, description="Glycémie à 2 h (mg/dL)")
    # … 6 autres champs
    age: int = Field(ge=1, le=120)
```

Les bornes ne remplacent pas la validation métier, mais elles arrêtent les valeurs absurdes (un âge négatif, une glycémie de 5 000) avant qu'elles n'atteignent le modèle.

### Préparer les données comme à l'entraînement

Le piège le plus courant d'un modèle en production ne fait aucune erreur visible : les données arrivent préparées **autrement** qu'à l'entraînement. Dans le jeu Pima, un 0 dans l'insuline signifie « mesure manquante », et `prepare.py` le remplace par une valeur manquante que le pipeline impute. Si l'API transmet le 0 tel quel, le modèle croit à une vraie insuline nulle. Mesuré sur le modèle des labs, pour le patient d'exemple :

| Insuline | Préparation | Probabilité estimée |
|---|---|---|
| 120 | — | 0,58 |
| 0 (inconnue) | même nettoyage qu'à l'entraînement | 0,61 |
| 0 (inconnue) | aucun nettoyage | **0,35** |

Aucune exception, aucun journal d'erreur : juste une estimation fausse. D'où une règle : le code de préparation est **partagé** entre l'entraînement et la prédiction (`predict.py` importe la liste des colonnes à nettoyer depuis `prepare.py`), et le modèle lui-même porte ce qu'il peut. Un pipeline scikit-learn entraîné sur un DataFrame retient par exemple ses colonnes et leur ordre dans `feature_names_in_`.

### Lancer et tester

```bash
uv run uvicorn api.main:app --reload        # http://localhost:8000/docs
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":45}'
```

Les tests utilisent `TestClient` : pas de serveur à lancer, les requêtes passent directement à l'application. Extrait de [tests/test_api.py](../projet-fil-rouge/tests/test_api.py) :

```python
from fastapi.testclient import TestClient

def test_predict_returns_prediction(client):
    r = client.post("/predict", json=PATIENT)
    assert r.status_code == 200
    assert r.json()["prediction"] in (0, 1)

def test_predict_validates_input(client):
    assert client.post("/predict", json={**PATIENT, "age": -3}).status_code == 422
```

### Configuration par l'environnement

Le chemin du modèle, le seuil de décision, les origines CORS : tout ce qui change d'un environnement à l'autre vient de **variables d'environnement**, lues par `pydantic-settings` ([api/settings.py](../projet-fil-rouge/api/settings.py)). En local un fichier `.env` suffit ; dans Docker et dans le cloud, ce sont les variables du conteneur. Le code ne change jamais.

## 3. Streamlit : une interface en Python

Streamlit transforme un script Python en page web : chaque widget (`st.slider`, `st.button`) est une ligne, et le script se réexécute à chaque interaction. C'est l'outil idéal pour une interface de démonstration ou un outil interne.

Extrait de [app/streamlit_app.py](../projet-fil-rouge/app/streamlit_app.py) :

```python
API_URL = os.getenv("API_URL", "").rstrip("/")

values = {"glucose": st.slider("Glycémie à 2 h (mg/dL)", 40, 250, 138), ...}

@st.cache_resource                       # le modèle n'est chargé qu'une fois
def load_predictor() -> Predictor:
    return Predictor(MODEL_PATH)

if st.button("Estimer le risque", type="primary"):
    try:
        if API_URL:                                              # mode API
            r = httpx.post(f"{API_URL}/predict", json=values, timeout=20)
            r.raise_for_status()
            st.session_state["result"] = r.json()
        else:                                                    # mode local
            st.session_state["result"] = load_predictor().predict_one(values)
    except Exception as exc:
        st.error(f"La prédiction a échoué : {exc}")

if "result" in st.session_state:                                 # survit aux réexécutions
    st.metric("Probabilité estimée", f"{st.session_state['result']['probability']:.0%}")
```

Trois points d'attention :

- **Le script se réexécute à chaque interaction.** Ce qui coûte va dans `@st.cache_resource` ; ce qui doit survivre d'une exécution à l'autre (le résultat) va dans `st.session_state`. Un second bouton placé sous le premier ne fonctionnerait jamais : au clic, le premier repasse à `False`.
- **Le mode est choisi par une variable d'environnement** (`API_URL`, lue dans un fichier `.env` en local). La même application se déploie seule sur Streamlit Community Cloud (mode local) ou devant une API sur Azure (mode API).
- **Tout appel réseau peut échouer** : `try/except`, délai d'attente, message lisible.

```bash
uv run streamlit run app/streamlit_app.py                                  # mode local
API_URL=http://localhost:8000 uv run streamlit run app/streamlit_app.py    # mode API
```

Une interface Streamlit se teste sans navigateur, avec `streamlit.testing.v1.AppTest` : on charge le script, on clique sur un bouton, on lit les valeurs affichées.

```python
from streamlit.testing.v1 import AppTest

def test_estimation_locale():                          # dans tests/test_app.py
    at = AppTest.from_file("../app/streamlit_app.py").run()   # chemin relatif au fichier de test
    at.button[0].click().run()
    assert at.metric[0].value == "58%"
```

## 4. Docker : emballer pour que ça tourne partout

### Le problème que Docker résout

`uv sync` garantit les mêmes bibliothèques Python. Mais pas la même version de Python système, pas les mêmes bibliothèques C, pas le même système d'exploitation. Une **image** Docker emballe tout cela ; un **conteneur** est une image en cours d'exécution. Le serveur cloud n'a besoin que de Docker.

### Le Dockerfile en deux étapes

![Image en deux étapes](../assets/diagrams/docker-layers.svg)

Extrait de [docker/api.Dockerfile](../projet-fil-rouge/docker/api.Dockerfile) :

```dockerfile
FROM ghcr.io/astral-sh/uv:0.9.17-python3.11-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group api   # couche mise en cache
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable --no-default-groups --group api
COPY models ./models

FROM python:3.11-slim-bookworm AS runtime
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

Pourquoi ces choix :

| Choix | Raison |
|---|---|
| Deux étapes (`builder`, `runtime`) | L'image finale ne contient ni uv, ni cache, ni sources : plus petite, moins de surface d'attaque |
| `COPY pyproject.toml uv.lock` avant le code | Les dépendances ne se réinstallent pas quand seul le code change (cache de couches) |
| `--no-default-groups --group api` | L'API n'embarque ni Streamlit ni MLflow |
| `USER appuser` | Un conteneur ne tourne pas en root |
| `${PORT}` | Cloud Run et d'autres plateformes imposent le port par cette variable |
| `COPY models` | Le modèle entraîné fait partie de l'image : on déploie un artefact figé, pas un entraînement |

### Les commandes

```bash
uv run dvc repro                                          # le modèle doit exister
docker build -f docker/api.Dockerfile -t diabetes-api .    # construit l'image
docker run --rm -p 8000:8000 diabetes-api                  # lance un conteneur, port 8000 publié
docker ps                                                  # conteneurs en cours
docker logs <id>                                           # ses journaux
docker exec -it <id> sh                                    # un shell dedans
docker image ls                                            # les images et leur taille
```

Le fichier `.dockerignore` exclut `.venv`, `.git`, `mlruns`, les données et les tests : le contexte envoyé à Docker reste petit. L'image de l'API pèse environ 700 Mo, dont l'essentiel pour numpy, scipy, pandas et scikit-learn ; `docker history` montre le poids de chaque couche.

Sous Windows, lancez ces commandes dans Git Bash. Pour un shell interactif dans un conteneur, Git Bash demande parfois `winpty docker exec -it <id> sh` ; pour une commande ponctuelle, préférez `docker exec <id> whoami` (sans `-it`).

### Docker Compose : plusieurs services ensemble

![Services Compose](../assets/diagrams/compose-services.svg)

[docker-compose.yml](../projet-fil-rouge/docker-compose.yml) décrit trois services : `api`, `app` et un serveur `mlflow`. Dans le réseau interne, chaque service est joignable par son nom : l'application appelle `http://api:8000`. Les ports publiés (`8000:8000`) rendent les services visibles depuis votre navigateur.

```bash
docker compose up --build        # construit et lance tout
docker compose ps                # état des services
docker compose logs -f api       # journaux d'un service
docker compose down              # arrête et supprime les conteneurs (les volumes restent)
```

## 5. Intégration continue avec GitHub Actions

### L'idée

Chaque `git push` déclenche, sur une machine de GitHub, la même séquence : installer, vérifier le style, tester, construire l'image, la publier. Si une étape échoue, les suivantes ne s'exécutent pas et vous êtes prévenu.

![Pipeline d'intégration continue](../assets/diagrams/ci-pipeline.svg)

### Le workflow

Extrait de [.github/workflows/ci.yml](../projet-fil-rouge/.github/workflows/ci.yml) :

```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request:

jobs:
  qualite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: uv run ruff check . && uv run ruff format --check .
      - run: uv run pytest

  image:
    needs: qualite
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    permissions: { packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --frozen && uv run dvc repro
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - id: meta
        uses: docker/metadata-action@v5          # nom en minuscules, tags latest et SHA
        with: { images: "ghcr.io/${{ github.repository }}/api", tags: "type=raw,value=latest\ntype=sha,prefix=" }
      - uses: docker/build-push-action@v6
        with: { context: ., file: docker/api.Dockerfile, push: true, tags: "${{ steps.meta.outputs.tags }}" }
```

Ce qu'il faut voir :

- **`uv sync --frozen`** : la CI installe exactement `uv.lock` ; si le lock n'est pas à jour, elle échoue au lieu de résoudre autre chose.
- **`needs: qualite`** : pas d'image si les tests échouent.
- **`dvc repro` dans la CI** : le modèle est réentraîné à partir du pipeline, donc l'image contient toujours un modèle cohérent avec le code.
- **La CI n'a accès qu'au dépôt.** Le fil rouge garde ses données brutes dans Git (elles sont petites). Dans votre projet, elles sont dans un remote DVC sur **votre** disque : la CI du lab 7 télécharge donc les données publiques du jeu Pima avant `dvc repro`, et DVC vérifie qu'elles ont la même empreinte. Avec un remote cloud (séance 3), un `dvc pull` remplace ce téléchargement.
- **Le nom d'une image Docker doit être en minuscules.** `docker/metadata-action` convertit `${{ github.repository }}` (`Marc1T/…` devient `marc1t/…`) et ajoute un tag immuable : le SHA du commit.
- **`ghcr.io`** : GitHub Container Registry, gratuit, authentifié par le jeton automatique du workflow. L'image publiée s'appelle `ghcr.io/<vous>/<depot>/api:latest` ; c'est elle que la séance 3 déploiera.

Avant le premier push, mettez le code au propre (`uv run ruff format .` puis `uv run ruff check --fix .`) : sinon le premier run échoue sur le style, pas sur le fond.

### Où trouver les résultats

Onglet **Actions** du dépôt : chaque exécution, chaque étape, les journaux. Onglet **Packages** : les images publiées. Un badge dans le README montre l'état du dernier run.

## 6. Récapitulatif

- Une API FastAPI sépare le modèle de ses clients ; Pydantic valide, `/docs` documente, `/health` surveille.
- Streamlit fait l'interface en Python ; une variable d'environnement choisit entre mode local et mode API.
- Docker emballe tout ; deux étapes pour une image petite et propre ; Compose pour lancer l'ensemble.
- GitHub Actions rejoue lint, tests, entraînement et construction à chaque push, et publie l'image.

**Devoir pour la séance 3** : pousser votre projet sur GitHub avec le workflow CI et obtenir un run vert. Vérifiez que l'image apparaît dans l'onglet Packages et rendez-la publique. Si vous n'avez pas encore de compte Azure for Students, c'est le moment : la vérification peut prendre plusieurs jours. Installez aussi [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli).

## 7. Auto-évaluation

Répondez sans regarder le cours ; les réponses sont publiées avec les solutions des labs.

1. Pourquoi charge-t-on le modèle dans `lifespan` plutôt que dans la fonction `predict` ?
2. Une requête envoie `"age": -3`. Quel code de statut l'API renvoie-t-elle, et quelle ligne de code l'a produit ?
3. Pourquoi l'API répond-elle `503` plutôt que `500` quand le modèle est absent ?
4. L'API reçoit une insuline à 0 et la transmet telle quelle au modèle. Qu'arrive-t-il, et comment l'éviter ?
5. Dans Streamlit, pourquoi range-t-on le résultat dans `st.session_state` ?
6. Pourquoi copie-t-on `pyproject.toml` et `uv.lock` **avant** le code dans le Dockerfile ?
7. Dans Docker Compose, l'interface appelle `http://api:8000`, mais votre navigateur `http://localhost:8000`. Pourquoi deux adresses ?
8. La CI de votre projet ne peut pas faire `dvc pull`. Pourquoi, et comment le lab 7 contourne-t-il le problème ?

## Pour aller plus loin (★★)

- **Journalisation structurée** : `logging` en JSON dans l'API, un identifiant par requête ; c'est ce que les plateformes cloud indexent.
- **Tests de contrat** : vérifier que `openapi.json` ne change pas sans le vouloir (snapshot).
- **Image plus légère** : `python:3.11-alpine` ? Souvent une fausse bonne idée pour numpy et scikit-learn (compilation). Mesurez avec `docker image ls`.
- **Cache de construction en CI** : `cache-from`/`cache-to` de `docker/build-push-action` pour accélérer les builds.
- **Un front sans Streamlit** : FastAPI peut servir une page HTML + JavaScript statique (`StaticFiles`) ; même API, autre client.
