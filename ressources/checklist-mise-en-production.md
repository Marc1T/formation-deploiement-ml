# Checklist de mise en production

À parcourir avant de déployer un projet ML. Chaque ligne renvoie à ce que la formation a mis en place.

![Huit vérifications](../assets/diagrams/checklist-prod.svg)

## Code et environnement

- [ ] Le code est dans Git, avec un `.gitignore` qui exclut `.venv`, `.env`, `mlruns`, les données et les modèles lourds.
- [ ] `pyproject.toml` déclare les dépendances, `uv.lock` est commité, `uv sync --frozen` réussit sur une machine neuve (la CI le prouve).
- [ ] Le code d'entraînement est un script dans `src/`, pas un notebook ; `params.yaml` centralise ce qui varie.
- [ ] Le style et les erreurs courantes sont vérifiés (`ruff check`, `ruff format --check`).

## Données et modèle

- [ ] Les données brutes sont versionnées : petites dans Git, sinon par DVC avec un remote partagé.
- [ ] Le pipeline est décrit dans `dvc.yaml` ; `dvc repro` régénère le modèle et `reports/metrics.json`.
- [ ] Chaque entraînement est un run MLflow (paramètres, métriques, modèle) ; le modèle déployé correspond à un run identifié (`mlflow_run_id` dans `model_info.json`).
- [ ] Les métriques de validation sont adaptées au problème (ici rappel et AUC plutôt qu'accuracy seule) et comparées à une base simple.
- [ ] Le prétraitement est dans le pipeline scikit-learn, pas dans du code à côté : l'API ne peut pas « oublier » une étape.

## Service

- [ ] L'API valide ses entrées (Pydantic, bornes), renvoie des codes de statut honnêtes (`422`, `503`) et expose `/health` et `/docs`.
- [ ] Le modèle est chargé une seule fois au démarrage ; une prédiction ne lit pas le disque.
- [ ] Les tests couvrent le cas nominal, l'entrée invalide et le modèle absent ; ils passent en CI.
- [ ] La configuration (chemin du modèle, seuil, URL de l'API, clés) vient de variables d'environnement ; `.env.example` documente les noms.

## Conteneur et livraison

- [ ] L'image Docker se construit en deux étapes, tourne en utilisateur non root, n'embarque que le groupe de dépendances utile, et contient le modèle comme artefact figé.
- [ ] `docker compose up` lance l'ensemble en local ; les sondes de santé fonctionnent.
- [ ] La CI construit et publie l'image avec un tag immuable (SHA ou version) en plus de `latest`.
- [ ] Les secrets de CI sont dans les *Secrets* du dépôt, jamais dans le workflow.

## Déploiement

- [ ] La plateforme interroge `/health` ; une alerte existe si le service ne répond plus.
- [ ] Les journaux sont consultables (`az containerapp logs show`, Cloud Logging) et contiennent assez d'information pour diagnostiquer une erreur.
- [ ] Les secrets sont injectés par la plateforme (secrets Container Apps, Secrets Streamlit, Secret Manager) ; `git grep` ne trouve aucune clé.
- [ ] Le service descend à zéro quand il n'est pas utilisé ; un budget avec alerte est défini ; le groupe de ressources sera supprimé en fin de projet.
- [ ] Le trafic réel est observé : distribution des entrées, taux d'erreurs, retours des utilisateurs ; un déclencheur de réentraînement est décidé.

## Pour un projet réel (au-delà de la formation)

- [ ] Authentification de l'API et CORS restreint à l'origine de l'interface.
- [ ] Données personnelles : base légale, minimisation, aucune donnée réelle envoyée à un service d'IA générative en palier gratuit.
- [ ] Sauvegarde et restauration du remote DVC et de la base MLflow.
- [ ] Procédure de retour arrière : révision précédente de la Container App, tag d'image précédent.
