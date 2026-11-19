# Lab 5 · Une interface Streamlit qui appelle l'API

**Durée** : 25 min · **Objectif** : un formulaire web qui envoie les mesures à l'API et affiche le risque, avec un mode local de secours.

Référence : [projet-fil-rouge/app/streamlit_app.py](../../projet-fil-rouge/app/streamlit_app.py).

## ★ Parcours de base

### 1. Installer

```bash
uv add --group app streamlit httpx python-dotenv
```

### 2. Le formulaire

`app/streamlit_app.py` :

```python
import os, sys
from pathlib import Path
import httpx
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))          # utile sur Streamlit Community Cloud
from diabete_lab.predict import Predictor      # noqa: E402

API_URL = os.getenv("API_URL", "").rstrip("/")

st.set_page_config(page_title="Risque de diabète", page_icon="🩺")
st.title("Estimation du risque de diabète")

col1, col2 = st.columns(2)
features = {
    "pregnancies": col1.slider("Grossesses", 0, 17, 1),
    "glucose": col2.slider("Glycémie (mg/dL)", 40, 250, 120),
    "blood_pressure": col1.slider("Pression diastolique", 30, 130, 72),
    "skin_thickness": col2.slider("Pli cutané (mm)", 0, 70, 25),
    "insulin": col1.slider("Insuline", 0, 600, 100, step=5),
    "bmi": col2.slider("IMC", 15.0, 60.0, 30.0, step=0.1),
    "diabetes_pedigree": col1.slider("Antécédents familiaux", 0.05, 2.5, 0.45, step=0.01),
    "age": col2.slider("Âge", 18, 90, 35),
}


@st.cache_resource
def load_predictor():
    return Predictor(os.getenv("MODEL_PATH", "models/model.joblib"))


if st.button("Estimer le risque", type="primary"):
    try:
        if API_URL:
            r = httpx.post(f"{API_URL}/predict", json=features, timeout=20)
            r.raise_for_status()
            result = r.json()
            st.caption(f"Mode API · {API_URL}")
        else:
            result = load_predictor().predict_one(features)
            st.caption("Mode local")
    except Exception as exc:
        st.error(f"La prédiction a échoué : {exc}")
    else:
        st.metric("Probabilité estimée", f"{result['probability']:.0%}")
        st.progress(result["probability"])
```

### 3. Les deux modes

```bash
# Mode local (le modèle est chargé dans l'application)
uv run streamlit run app/streamlit_app.py

# Mode API (l'API du lab 4 tourne dans un autre terminal)
#   bash :        API_URL=http://localhost:8000 uv run streamlit run app/streamlit_app.py
#   PowerShell :  $env:API_URL="http://localhost:8000"; uv run streamlit run app/streamlit_app.py
```

Arrêtez l'API pendant que l'interface est en mode API, cliquez : le message d'erreur s'affiche proprement. C'est l'intérêt du `try/except` autour de l'appel réseau.

### 4. Un fichier `.env` plutôt que des variables à la main

Créez `.env` (et ajoutez-le au `.gitignore`) :

```
API_URL=http://localhost:8000
```

En haut de l'application : `from dotenv import load_dotenv; load_dotenv()`. Relancez : le mode API est actif sans rien exporter.

## ★★ Aller plus loin

- **Barre latérale d'état** : `st.sidebar` qui appelle `/health` au chargement et affiche vert / rouge.
- **Exemples pré-remplis** : deux boutons « profil à faible risque » / « profil à risque élevé » qui remplissent les sliders via `st.session_state`.
- **Historique** : garder les dix dernières estimations dans `st.session_state` et les afficher dans un `st.dataframe`.
- **Thème** : `.streamlit/config.toml` avec `primaryColor` aux couleurs de votre projet.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| L'application se relance en boucle | normal : Streamlit réexécute le script à chaque interaction | mettre le coûteux dans `@st.cache_resource` |
| `ConnectError` en mode API | l'API n'est pas lancée, ou mauvais port | vérifier http://localhost:8000/health |
| `ModuleNotFoundError: diabete_lab` | `src/` pas dans le chemin | le `sys.path.insert` en haut du script, ou `uv run` depuis la racine |
| Les sliders reviennent à zéro | la clé `key=` manque pour `session_state` | donner un `key` à chaque widget |

## Ce qu'il faut retenir

Une interface = des widgets + un appel à une fonction de prédiction. Le mode (local / API) est de la configuration, pas du code. Solution complète : publiée après la séance.
