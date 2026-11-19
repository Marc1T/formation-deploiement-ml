# Déployer l'application sur Streamlit Community Cloud

Gratuit, sans carte bancaire, connexion avec GitHub. C'est le déploiement « garanti » de la séance 3 : chaque étudiant obtient une URL publique en quelques minutes.

## Ce que Streamlit Cloud fait

1. Il clone votre dépôt GitHub public.
2. Il installe les dépendances listées dans `requirements.txt` (à la racine).
3. Il lance `streamlit run <fichier>` et expose l'application sur `https://<nom>.streamlit.app`.

Les secrets (clé Gemini, URL de l'API) se saisissent dans l'interface, jamais dans le code.

## Étapes

1. **Pousser le projet sur GitHub** (dépôt public) : ce dossier `projet-fil-rouge` doit être la racine du dépôt, ou vous indiquerez le sous-chemin du fichier principal.
2. **Vérifier `requirements.txt`** : il est généré depuis `uv.lock` pour rester cohérent avec votre environnement :
   ```bash
   uv export --format requirements-txt --no-dev --no-default-groups --group app --no-hashes --no-emit-project -o requirements.txt
   ```
3. Aller sur [share.streamlit.io](https://share.streamlit.io) → **Create app** → **Deploy a public app from GitHub**.
4. Renseigner : dépôt, branche `main`, fichier principal `app/streamlit_app.py`, URL souhaitée.
5. **Advanced settings** : version de Python `3.11`, puis coller les secrets au format TOML :
   ```toml
   # API_URL = "https://diabetes-api.<region>.azurecontainerapps.io"   # sinon mode local
   # GEMINI_API_KEY = "AIza..."
   ```
6. **Deploy**. Les journaux de construction s'affichent ; la première installation prend 2 à 4 minutes.

## Le modèle en production : trois options

| Option | Comment | Quand |
|---|---|---|
| Mode API | Secret `API_URL` vers votre API Azure / Cloud Run | Vous avez déployé l'API (lab 9) |
| Modèle téléchargé | Secret `MODEL_URL` (ex. un asset d'une *release* GitHub contenant `model.joblib`) | Vous voulez servir exactement le modèle validé, sans API |
| Repli de démonstration | Rien à faire : l'application s'entraîne au démarrage depuis `data/raw/diabetes.csv` | Démo rapide ; à ne pas faire en vrai projet |

Le repli existe pour que le déploiement réussisse à coup sûr pendant la séance. Dans un vrai projet, le modèle servi doit être un artefact versionné (DVC, MLflow Registry ou release), jamais réentraîné silencieusement au démarrage.

## Dépannage

- `ModuleNotFoundError: diabetes_ml` : le fichier principal ajoute `src/` au chemin Python ; vérifiez que le dossier `src/diabetes_ml` est bien dans le dépôt.
- Application endormie : sans visite pendant plusieurs jours, Streamlit met l'application en veille ; un clic la réveille.
- Dépassement de mémoire : l'application charge le modèle une seule fois (`st.cache_resource`) ; évitez d'importer `mlflow` ou `dvc` dans l'application.
