# Projet fil rouge : prédire le risque de diabète, du notebook au cloud

Ce dépôt est le support pratique de la formation « Déployer un modèle ML et un site web ». Il contient une chaîne complète et fonctionnelle :

| Brique | Outil | Fichiers |
|---|---|---|
| Environnement reproductible | uv | `pyproject.toml`, `uv.lock`, `.python-version` |
| Pipeline de données et d'entraînement | DVC | `dvc.yaml`, `params.yaml`, `src/diabetes_ml/` |
| Suivi des expériences | MLflow | `src/diabetes_ml/train.py`, `mlflow.db` |
| API de prédiction | FastAPI | `api/` |
| Interface web | Streamlit | `app/` |
| Tests | pytest | `tests/` |
| Conteneurs | Docker, Docker Compose | `docker/`, `docker-compose.yml` |
| Intégration continue | GitHub Actions | `.github/workflows/` |
| Déploiement | Azure Container Apps, Cloud Run, Streamlit Cloud, Render | `deploy/` |

Le jeu de données est *Pima Indians Diabetes* (768 patientes, 8 mesures cliniques, cible binaire). Il tient dans un CSV de 23 Ko : tout s'entraîne en quelques secondes, ce qui laisse le temps de se concentrer sur le déploiement. Usage pédagogique uniquement : ce modèle n'est pas un outil médical.

## Démarrage en 5 commandes

```bash
uv sync                                  # 1. environnement + dépendances (Python 3.11 installé si besoin)
uv run dvc repro                         # 2. prepare -> train -> evaluate ; écrit models/ et reports/
uv run pytest                            # 3. tests du modèle et de l'API
uv run uvicorn api.main:app --reload     # 4. API sur http://localhost:8000/docs
uv run streamlit run app/streamlit_app.py  # 5. interface sur http://localhost:8501
```

Pour voir les expériences : `uv run mlflow ui --backend-store-uri sqlite:///mlflow.db` puis ouvrir http://localhost:5000.

## Structure

```
projet-fil-rouge/
├── data/raw/diabetes.csv        données brutes (versionnées dans Git : petites)
├── data/processed/              train.csv, test.csv (produits par DVC, ignorés par Git)
├── src/diabetes_ml/
│   ├── config.py                lecture de params.yaml
│   ├── data.py                  étape prepare : nettoyage, découpage
│   ├── train.py                 étape train : pipeline scikit-learn + MLflow
│   ├── evaluate.py              étape evaluate : métriques -> reports/metrics.json
│   └── predict.py               Predictor : chargement du modèle, prédiction unitaire
├── api/                         FastAPI : main.py, schemas.py, settings.py
├── app/streamlit_app.py         interface (mode API ou mode local)
├── tests/                       pytest : modèle et API
├── docker/                      api.Dockerfile, app.Dockerfile
├── docker-compose.yml           api + app + serveur MLflow
├── deploy/                      scripts Azure, GCP, Render, guide Streamlit Cloud
└── .github/workflows/           ci.yml (lint, tests, image), deploy-azure.yml
```

## Le pipeline

```
data/raw/diabetes.csv ──► prepare ──► data/processed/{train,test}.csv ──► train ──► models/model.joblib ──► evaluate ──► reports/metrics.json
                               ▲                                            ▲                                    ▲
                               └──────────────────── params.yaml ───────────┴────────────────────────────────────┘
```

- `uv run dvc repro` exécute uniquement les étapes dont une dépendance a changé.
- `uv run dvc dag` affiche le graphe ; `uv run dvc metrics show` les métriques ; `uv run dvc params diff` les paramètres modifiés.
- Chaque entraînement crée un run MLflow (paramètres, métriques de validation croisée, modèle). L'évaluation rattache les métriques de test au même run.

Essayez : changez `train.model` en `logistic_regression` dans `params.yaml`, relancez `uv run dvc repro`, comparez dans MLflow.

## L'API

| Route | Rôle |
|---|---|
| `GET /health` | Sonde : l'API répond-elle, le modèle est-il chargé ? |
| `GET /model` | Métadonnées du modèle servi (type, date, métriques, run MLflow) |
| `POST /predict` | Prédiction pour un patient (JSON validé par Pydantic) |
| `GET /docs` | Documentation interactive (OpenAPI) |

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":45}'
```

Configuration par variables d'environnement (ou `.env`, voir `.env.example`) : `MODEL_PATH`, `THRESHOLD`.

## L'application web

- Sans `API_URL` : mode local, le modèle est chargé dans l'application.
- Avec `API_URL=http://localhost:8000` : mode API, l'application appelle FastAPI.
- Avec `GEMINI_API_KEY` (Google AI Studio) : un bouton génère une explication en langage naturel de l'estimation.

## Docker

```bash
uv run dvc repro                 # le modèle doit exister : il est copié dans l'image
docker compose up --build        # api :8000, app :8501, mlflow :5000
```

Les images sont construites en deux étapes avec uv : les dépendances du groupe concerné (`api` ou `app`) seulement, puis une image `python:3.11-slim` sans outils de build, avec un utilisateur non root.

## Déploiement

| Cible | Quand | Comment |
|---|---|---|
| Streamlit Community Cloud | Déploiement gratuit garanti de l'application | [deploy/streamlit-cloud.md](deploy/streamlit-cloud.md) |
| Azure Container Apps | API conteneurisée, avec Azure for Students | `deploy/azure/deploy.ps1` ou `deploy.sh` |
| Google Cloud Run | Équivalent GCP (démonstration) | `deploy/gcp/deploy.sh` |
| Render | Alternative gratuite pour l'API | `deploy/render.yaml` |

Les workflows GitHub Actions s'activent quand ce dossier est la racine d'un dépôt GitHub : `ci.yml` publie l'image de l'API dans `ghcr.io`, `deploy-azure.yml` met à jour la Container App à la demande.

## Adapter à votre propre projet

1. Remplacez `data/raw/diabetes.csv` et la liste `FEATURES` dans `src/diabetes_ml/data.py`.
2. Adaptez `build_pipeline` dans `train.py` et les schémas Pydantic dans `api/schemas.py`.
3. Mettez à jour les sliders dans `app/streamlit_app.py`.
4. `uv run dvc repro`, `uv run pytest`, puis les mêmes commandes de déploiement.

## Licence

Code sous licence MIT. Jeu de données Pima Indians Diabetes : National Institute of Diabetes and Digestive and Kidney Diseases, diffusé à des fins pédagogiques.
