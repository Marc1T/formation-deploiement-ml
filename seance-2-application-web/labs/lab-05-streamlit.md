# Lab 5 · Une interface Streamlit qui appelle l'API

**Durée** : 25 min · **Objectif** : un formulaire web qui envoie les mesures à l'API et affiche le risque, avec un mode local qui se passe de l'API.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab` du lab 4, avec son API et `src/diabete_lab/predict.py`. Référence : [projet-fil-rouge/app/streamlit_app.py](../../projet-fil-rouge/app/streamlit_app.py).

## ★ Parcours de base

### 1. Installer

```bash
uv add --group app streamlit httpx python-dotenv
```

### 2. Le formulaire

Créez `app/streamlit_app.py` :

```python
"""Interface web : estimation du risque de diabète."""
import os
import sys
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))      # pour trouver diabete_lab même s'il n'est pas installé
from diabete_lab.predict import Predictor  # noqa: E402

load_dotenv(ROOT / ".env")                 # lit .env s'il existe (local uniquement)
API_URL = os.getenv("API_URL", "").rstrip("/")
MODEL_PATH = os.getenv("MODEL_PATH", str(ROOT / "models" / "model.joblib"))

st.set_page_config(page_title="Risque de diabète")
st.title("Estimation du risque de diabète")
st.caption("Exercice pédagogique : ce n'est pas un outil médical.")

col1, col2 = st.columns(2)
values = {
    "pregnancies": col1.slider("Grossesses", 0, 17, 2),
    "glucose": col2.slider("Glycémie à 2 h (mg/dL)", 40, 250, 138),
    "blood_pressure": col1.slider("Pression diastolique (mm Hg)", 30, 130, 72),
    "skin_thickness": col2.slider("Pli cutané (mm)", 0, 70, 35),
    "insulin": col1.slider("Insuline (µU/mL)", 0, 600, 120, step=5),
    "bmi": col2.slider("IMC", 15.0, 60.0, 33.6, step=0.1),
    "diabetes_pedigree": col1.slider("Antécédents familiaux", 0.05, 2.5, 0.62, step=0.01),
    "age": col2.slider("Âge", 18, 90, 45),
}


@st.cache_resource
def load_predictor() -> Predictor:
    return Predictor(MODEL_PATH)


def predict(values: dict) -> dict:
    if API_URL:                                            # mode API
        r = httpx.post(f"{API_URL}/predict", json=values, timeout=20)
        r.raise_for_status()
        return r.json()
    return load_predictor().predict_one(values)            # mode local


if st.button("Estimer le risque", type="primary"):
    try:
        st.session_state["result"] = predict(values)
        st.session_state["values"] = values
    except Exception as exc:
        st.error(f"La prédiction a échoué : {exc}")

if "result" in st.session_state:
    result = st.session_state["result"]
    st.metric("Probabilité estimée", f"{result['probability']:.0%}")
    st.progress(result["probability"])
    st.caption("Mode API · " + API_URL if API_URL else "Mode local")
```

Trois détails :

- `sys.path.insert` : en local, `diabete_lab` est installé par uv ; sur Streamlit Community Cloud (séance 3), il ne le sera pas.
- `@st.cache_resource` : Streamlit réexécute tout le script à chaque interaction ; sans cache, le modèle serait rechargé à chaque mouvement de curseur.
- `st.session_state` : garde le résultat entre deux exécutions du script. Sans lui, le résultat disparaîtrait au moindre clic ailleurs (au lab 11, vous ajouterez un second bouton).

### 3. Mode local

```bash
uv run streamlit run app/streamlit_app.py
```

Le navigateur s'ouvre sur http://localhost:8501. Cliquez sur **Estimer le risque**.

> **Point de contrôle** : `Probabilité estimée 58%`, et la mention « Mode local ».

### 4. Mode API

Dans un second terminal, lancez l'API du lab 4 : `uv run uvicorn api.main:app`. Puis créez un fichier `.env` à la racine du projet (il est déjà dans le `.gitignore`) :

```
API_URL=http://localhost:8000
```

Arrêtez Streamlit (`Ctrl+C`) et relancez-le : la variable est lue au démarrage.

> **Point de contrôle** : même résultat, `58%`, avec la mention `Mode API · http://localhost:8000`.

Arrêtez l'API et cliquez à nouveau : un message d'erreur s'affiche proprement, l'application ne plante pas. C'est le rôle du `try/except` autour de l'appel réseau.

Supprimez ou commentez la ligne de `.env` pour revenir au mode local, puis commitez :

```bash
git add -A
git commit -m "Interface Streamlit (modes local et API)"
```

## ★★ Aller plus loin

- **Tester l'interface sans navigateur** avec `streamlit.testing.v1.AppTest` : `tests/test_app.py`

  ```python
  from streamlit.testing.v1 import AppTest


  def test_estimation_locale():
      # le chemin est relatif au fichier de test (tests/), pas au dossier courant
      at = AppTest.from_file("../app/streamlit_app.py").run()
      at.button[0].click().run()
      assert at.metric[0].value == "58%"
  ```

  `uv run pytest` lance alors 4 tests, dont celui-ci.

- **Barre latérale d'état** : `st.sidebar` qui appelle `/health` au chargement et affiche vert ou rouge.
- **Exemples pré-remplis** : deux boutons « profil à faible risque » (1 %) et « profil à risque élevé » (81 %) qui remplissent les curseurs via `st.session_state` (voir le fil rouge).
- **Historique** : garder les dix dernières estimations dans `st.session_state` et les afficher dans un `st.dataframe`.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| L'application se recharge à chaque mouvement | normal : Streamlit réexécute le script | ce qui coûte va dans `@st.cache_resource` |
| `ConnectError` en mode API | API arrêtée ou mauvais port | vérifier http://localhost:8000/health |
| Le mode ne change pas après avoir modifié `.env` | `.env` est lu au démarrage | arrêter et relancer Streamlit |
| `ModuleNotFoundError: diabete_lab` | `src/` absent du chemin | garder le `sys.path.insert` en tête du script |
| `FileNotFoundError: models/model.joblib` en mode local | modèle pas encore entraîné | `uv run dvc repro` |
| Le résultat disparaît après un clic | résultat gardé dans une variable locale | le ranger dans `st.session_state` |

## À retenir

- **Une interface, ce sont des widgets et un appel à une fonction de prédiction** ; Streamlit en fait une page web en Python.
- **Le script se réexécute à chaque interaction** : on met en cache ce qui coûte (`st.cache_resource`) et on garde l'état dans `st.session_state`.
- **Le mode local ou API est de la configuration** (`API_URL`), pas du code : la même application servira sur Streamlit Cloud et derrière Azure.
- **Tout appel réseau peut échouer** : `try/except`, délai d'attente et message lisible.

## Solution

Solution complète : publiée après la séance.
