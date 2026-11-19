# Liens utiles

## Documentation officielle des outils

| Outil | Documentation | À lire en premier |
|---|---|---|
| uv | https://docs.astral.sh/uv/ | *Projects*, *Dependency groups*, *Docker integration* |
| DVC | https://dvc.org/doc | *Get Started: Data Pipelines*, *Remote storage* |
| MLflow | https://mlflow.org/docs/latest/ | *Tracking*, *Model Registry*, *Deploying models* |
| FastAPI | https://fastapi.tiangolo.com/ | *Tutorial*, *Lifespan events*, *Testing* |
| Pydantic | https://docs.pydantic.dev/ | *Fields*, *Settings management* |
| Streamlit | https://docs.streamlit.io/ | *Caching*, *Secrets management*, *Deploy on Community Cloud* |
| Docker | https://docs.docker.com/ | *Multi-stage builds*, *Compose*, *Build cache* |
| GitHub Actions | https://docs.github.com/actions | *Workflow syntax*, *Publishing Docker images*, *Encrypted secrets* |
| Azure CLI | https://learn.microsoft.com/cli/azure/ | `az containerapp`, `az acr`, `az group` |
| Azure Container Apps | https://learn.microsoft.com/azure/container-apps/ | *Quickstart: deploy an existing image*, *Scaling* |
| Azure Machine Learning | https://learn.microsoft.com/azure/machine-learning/ | *What is Azure ML*, *MLflow and Azure ML*, *Managed online endpoints* |
| Google Cloud Run | https://cloud.google.com/run/docs | *Deploy a container*, *Container runtime contract* |
| Vertex AI | https://cloud.google.com/vertex-ai/docs | *Custom containers for prediction*, *Model Registry*, *Model Monitoring* |
| Google AI Studio / Gemini API | https://ai.google.dev/gemini-api/docs | *Quickstart*, *Rate limits*, *Pricing*, SDK `google-genai` |

## Offres et programmes

- Azure for Students : https://azure.microsoft.com/free/students
- Azure Education Hub (FAQ) : https://learn.microsoft.com/azure/education-hub/
- GitHub Student Developer Pack : https://education.github.com/pack
- Google Cloud for Education (crédits enseignants) : https://cloud.google.com/edu
- Streamlit Community Cloud : https://share.streamlit.io
- Render (plan gratuit) : https://render.com/pricing

## Jeu de données

- Pima Indians Diabetes : National Institute of Diabetes and Digestive and Kidney Diseases ; copie utilisée : https://github.com/jbrownlee/Datasets (`pima-indians-diabetes.data.csv`). Variables : grossesses, glycémie, pression diastolique, pli cutané, insuline, IMC, fonction d'antécédents, âge, issue.

## Pour aller plus loin

- *Designing Machine Learning Systems*, Chip Huyen (O'Reilly) : la vue d'ensemble de la mise en production.
- *Made With ML* (madewithml.com) : un cours gratuit qui suit la même progression, notebook → service → déploiement.
- Documentation *Twelve-Factor App* (12factor.net) : configuration par l'environnement, journaux, processus sans état.
- Pre-commit (pre-commit.com) : exécuter ruff et d'autres vérifications avant chaque commit.
- Hugging Face Hub : partager modèles et jeux de données (les Spaces Docker sont devenus payants en 2026 ; à vérifier).

## Dans ce dépôt

- [README principal](../README.md) · [Prérequis](../00-prerequis/README.md)
- [Séance 1](../seance-1-fondations/README.md) · [Séance 2](../seance-2-application-web/README.md) · [Séance 3](../seance-3-cloud/README.md)
- [Projet fil rouge](../projet-fil-rouge/README.md)
- [Comparatif cloud](comparatif-cloud.md) · [Checklist](checklist-mise-en-production.md) · [Glossaire](glossaire.md)
