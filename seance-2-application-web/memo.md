# Mémo · Séance 2 · FastAPI, Streamlit, Docker, GitHub Actions

Toutes les commandes de la séance sur une page. Terminal : Git Bash sous Windows, Terminal sous macOS et Linux.

## FastAPI

| Commande | Effet |
|---|---|
| `uv add --group api fastapi "uvicorn[standard]"` | Installe FastAPI et son serveur |
| `uv run uvicorn api.main:app --reload` | Lance l'API sur http://localhost:8000 (recharge à chaque modification) |
| `MODEL_PATH=autre.joblib uv run uvicorn api.main:app` | Même API, autre configuration |
| http://localhost:8000/docs | Documentation interactive (*Try it out*) |
| `curl http://localhost:8000/health` | Sonde de santé |
| `curl -X POST …/predict -H "Content-Type: application/json" -d '{…}'` | Une prédiction |

```python
@asynccontextmanager
async def lifespan(app):            # exécuté une fois au démarrage
    state["predictor"] = Predictor(MODEL_PATH)
    yield

@app.post("/predict", response_model=PredictionOut)
def predict(patient: PatientFeatures):          # 422 automatique si l'entrée est invalide
    if state["predictor"] is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    return state["predictor"].predict_one(patient.model_dump())
```

| Code | Sens |
|---|---|
| `200` | OK |
| `422` | Entrée invalide (Pydantic) |
| `500` | Erreur non prévue dans le code |
| `503` | Service pas prêt (modèle absent) |

Tests : `with TestClient(app) as client:` (le `with` déclenche le `lifespan`), et `[tool.pytest.ini_options] pythonpath = ["."]` dans `pyproject.toml`.

## Streamlit

| Commande ou élément | Effet |
|---|---|
| `uv run streamlit run app/streamlit_app.py` | Lance l'interface sur http://localhost:8501 |
| `@st.cache_resource` | Garde un objet coûteux (le modèle) entre deux exécutions du script |
| `st.session_state["result"] = …` | Garde une valeur (le résultat) entre deux interactions |
| `.env` + `load_dotenv()` | Configuration locale, jamais commitée |
| `AppTest.from_file("app/streamlit_app.py").run()` | Test de l'interface sans navigateur |

## Docker

| Commande | Effet |
|---|---|
| `docker build -f docker/api.Dockerfile -t diabete-api .` | Construit une image |
| `docker image ls` / `docker history diabete-api` | Images et poids de chaque couche |
| `docker run --rm -d -p 8000:8000 --name api-test diabete-api` | Lance un conteneur en arrière-plan |
| `docker ps` / `docker logs api-test` | Conteneurs en cours / journaux |
| `docker exec api-test whoami` | Une commande dans le conteneur |
| `docker stop api-test` | Arrête (et supprime, avec `--rm`) |
| `docker run -e THRESHOLD=0.6 …` | Même image, autre configuration |

Dockerfile en deux étapes : `FROM …uv… AS builder` → `COPY pyproject.toml uv.lock` → `uv sync --frozen --no-install-project --no-default-groups --group api` → `COPY src` → `uv sync --frozen --no-editable …` ; puis `FROM python:3.11-slim` → `COPY --from=builder /app/.venv` → `USER appuser`.

## Docker Compose

| Commande | Effet |
|---|---|
| `docker compose up --build -d` | Construit et lance tous les services |
| `docker compose ps` | État des services |
| `docker compose logs -f api` | Journaux d'un service |
| `docker compose exec -T app python -c "…"` | Une commande dans un service (`-T` sous Git Bash) |
| `docker compose down` | Arrête et supprime les conteneurs |

Dans le réseau de Compose, un service se joint par son nom : `http://api:8000`. Depuis votre machine : `http://localhost:8000`.

## GitHub Actions

| Élément | Effet |
|---|---|
| `.github/workflows/ci.yml` | Le workflow, déclenché par `on: push` et `on: pull_request` |
| `uv sync --frozen` | Installe exactement `uv.lock`, échoue s'il n'est pas à jour |
| `needs: qualite` | Un job attend le succès d'un autre |
| `permissions: packages: write` | Droit de publier une image sur ghcr.io |
| `docker/metadata-action@v5` | Nom d'image en minuscules, tags `latest` et SHA |
| `uv run ruff format . && uv run ruff check --fix .` | À lancer avant de pousser |
| `[tool.ruff.lint] select = ["E4", "E7", "E9", "F", "I"]` | Règles explicites : la CI ne dépend pas de la version de ruff |

Onglet **Actions** : les exécutions et leurs journaux. Onglet **Packages** : les images, à rendre publiques pour le déploiement.
