# Glossaire

Les termes tels qu'ils sont utilisés dans la formation, avec la séance où ils apparaissent.

| Terme | Définition | Séance |
|---|---|---|
| **Artefact** | Un fichier produit par une étape : modèle entraîné, métriques, image Docker. Il se versionne, ne se régénère pas en silence. | 1 |
| **API (REST)** | Un service qui répond à des requêtes HTTP sur des URL (endpoints) avec du JSON. | 2 |
| **Azure Container Apps** | Service Azure qui exécute des conteneurs avec ingress HTTPS, journaux et mise à l'échelle automatique, y compris à zéro. | 3 |
| **Azure for Students** | Offre étudiante : 100 $ de crédit et services gratuits, sans carte bancaire, vérifiée par e-mail académique. | 0, 3 |
| **Azure Machine Learning** | Plateforme ML managée de Microsoft : données, notebooks, jobs, registre (MLflow), endpoints, monitoring. | 3 |
| **CI (intégration continue)** | Exécution automatique des vérifications (lint, tests, construction) à chaque modification du code. | 2 |
| **Cloud Run** | Service Google Cloud qui exécute des conteneurs sans serveur, facturé à la requête, port imposé par `PORT`. | 3 |
| **Conteneur** | Une image en cours d'exécution, isolée du système hôte. | 2 |
| **Démarrage à froid** | Délai de la première requête quand un service remonte de zéro instance. | 3 |
| **Dépendance transitive** | Bibliothèque installée parce qu'une autre en a besoin ; figée par `uv.lock`. | 1 |
| **DVC** | Data Version Control : versionne les fichiers lourds (pointeur dans Git, contenu dans un remote) et décrit le pipeline (`dvc.yaml`). | 1 |
| **Dérive (drift)** | Écart progressif entre les données vues en production et celles de l'entraînement. | 3 |
| **Endpoint** | Une route d'API (`POST /predict`) ; chez Azure ML et Vertex AI, un modèle déployé et son URL. | 2, 3 |
| **Environnement (Python)** | Dossier `.venv` contenant un interpréteur et des bibliothèques installées ; recréé par `uv sync`. | 1 |
| **Expérience / run (MLflow)** | Une expérience regroupe des runs ; un run est une exécution avec ses paramètres, métriques et artefacts. | 1 |
| **Fragment de secret** | Une partie de clé affichée pour vérification ; une clé complète ne s'affiche jamais. | 3 |
| **Gemini / Google AI Studio** | Modèles d'IA générative de Google ; AI Studio est l'interface gratuite pour prototyper et obtenir une clé. | 3 |
| **ghcr.io** | GitHub Container Registry : stockage des images Docker lié à un dépôt GitHub. | 2 |
| **Groupe de ressources** | Dossier Azure contenant toutes les ressources d'un projet ; se supprime d'un coup. | 3 |
| **Image Docker** | Paquet figé : système, Python, bibliothèques, code, modèle. Construite depuis un `Dockerfile`. | 2 |
| **Ingress** | L'exposition réseau d'un conteneur (HTTPS public ou interne). | 3 |
| **JSON** | Format texte d'échange de données (`{"glucose": 138}`). | 2 |
| **Lifespan (FastAPI)** | Code exécuté au démarrage et à l'arrêt de l'application ; sert à charger le modèle une fois. | 2 |
| **Lock file** | `uv.lock` : la liste exacte de toutes les versions installées, avec leurs empreintes. | 1 |
| **Model Registry** | Catalogue de modèles nommés et versionnés (MLflow, Azure ML, Vertex AI). | 1, 3 |
| **MLflow** | Outil de suivi d'expériences, de stockage de modèles et de registre. | 1 |
| **Multi-étapes (Docker)** | Dockerfile en plusieurs `FROM` : on construit dans une image, on exécute dans une autre, plus petite. | 2 |
| **Pipeline (DVC)** | Graphe d'étapes reliées par leurs fichiers ; `dvc repro` relance ce qui a changé. | 1 |
| **Pipeline (scikit-learn)** | Enchaînement imputation → standardisation → modèle, sauvegardé comme un seul objet. | 1, 2 |
| **Pydantic** | Bibliothèque de validation de données par types ; base des schémas FastAPI et de `pydantic-settings`. | 2 |
| **Région** | Emplacement géographique des serveurs cloud (`francecentral`, `southafricanorth`, `europe-west1`). | 3 |
| **Remote (DVC)** | Stockage du contenu des fichiers suivis : dossier partagé, Azure Blob, GCS, S3. | 1 |
| **Scale-to-zero** | Aucune instance quand il n'y a pas de trafic ; coût quasi nul, démarrage à froid. | 3 |
| **Secret** | Valeur sensible (clé, mot de passe) fournie à l'application par la plateforme, jamais écrite dans le code. | 3 |
| **Serverless** | Modèle où le fournisseur gère serveurs et montée en charge ; on fournit code ou conteneur. | 3 |
| **Streamlit** | Bibliothèque Python qui transforme un script en interface web. | 2 |
| **Streamlit Community Cloud** | Hébergement gratuit d'applications Streamlit depuis GitHub. | 3 |
| **TestClient** | Client de test FastAPI : envoie des requêtes à l'application sans serveur. | 2 |
| **uv** | Gestionnaire de projets Python : installe Python, résout et fige les dépendances, exécute dans l'environnement. | 1 |
| **Vertex AI** | Plateforme ML managée de Google : Workbench, Training, Model Registry, Endpoints, Model Monitoring, Vertex AI Studio. | 3 |
| **Workflow (GitHub Actions)** | Fichier YAML décrivant des jobs exécutés par GitHub à chaque événement (push, pull request). | 2 |
