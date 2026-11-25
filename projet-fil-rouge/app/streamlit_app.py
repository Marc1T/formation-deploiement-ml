"""Interface web du projet fil rouge (Streamlit).

Deux modes, choisis automatiquement :
  - mode API    : si la variable API_URL est définie, l'application appelle l'API FastAPI ;
  - mode local  : sinon, elle charge le modèle (models/model.joblib) directement.

Lancer :  uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:  # Streamlit Community Cloud n'installe pas le package
    sys.path.insert(0, str(ROOT / "src"))

from diabetes_ml.data import FEATURES  # noqa: E402
from diabetes_ml.predict import Predictor, risk_level  # noqa: E402

try:  # .env en local ; sans effet en production
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:  # pragma: no cover
    pass


# ---------------------------------------------------------------- configuration
def setting(name: str, default: str = "") -> str:
    """Variable d'environnement, sinon secrets Streamlit, sinon valeur par défaut."""
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, AttributeError, KeyError):
        return default


API_URL = setting("API_URL").rstrip("/")
MODEL_PATH = setting("MODEL_PATH", str(ROOT / "models" / "model.joblib"))
MODEL_URL = setting("MODEL_URL")
GEMINI_API_KEY = setting("GEMINI_API_KEY")
GEMINI_MODEL = setting("GEMINI_MODEL", "gemini-flash-latest")

# libellé, min, max, valeur par défaut, pas
LABELS = {
    "pregnancies": ("Grossesses", 0, 17, 1, 1),
    "glucose": ("Glycémie à 2 h (mg/dL)", 40, 250, 120, 1),
    "blood_pressure": ("Pression diastolique (mm Hg)", 30, 130, 72, 1),
    "skin_thickness": ("Pli cutané (mm)", 0, 70, 25, 1),
    "insulin": ("Insuline (µU/mL)", 0, 600, 100, 5),
    "bmi": ("IMC", 15.0, 60.0, 30.0, 0.1),
    "diabetes_pedigree": ("Antécédents familiaux (score)", 0.05, 2.5, 0.45, 0.01),
    "age": ("Âge", 18, 90, 35, 1),
}
EXAMPLES = {
    "Profil à faible risque": dict(
        pregnancies=1,
        glucose=92,
        blood_pressure=66,
        skin_thickness=22,
        insulin=70,
        bmi=24.5,
        diabetes_pedigree=0.2,
        age=26,
    ),
    "Profil à risque élevé": dict(
        pregnancies=6,
        glucose=175,
        blood_pressure=88,
        skin_thickness=38,
        insulin=240,
        bmi=36.8,
        diabetes_pedigree=1.1,
        age=52,
    ),
}


# ---------------------------------------------------------------- modèle local
@st.cache_resource(show_spinner="Chargement du modèle…")
def load_predictor(path: str) -> Predictor:
    p = Path(path)
    if not p.exists() and MODEL_URL:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(httpx.get(MODEL_URL, follow_redirects=True, timeout=60).content)
    if not p.exists():
        # Repli de démonstration (Streamlit Community Cloud sans artefact) :
        # on entraîne rapidement à partir des données versionnées dans le dépôt.
        from diabetes_ml.data import clean, load_raw, split
        from diabetes_ml.model import fit, save

        train_df, _ = split(clean(load_raw(ROOT / "data" / "raw" / "diabetes.csv")), 0.2, 42)
        pipe, metrics = fit(train_df, {"model": "logistic_regression", "C": 1.0})
        save(
            pipe,
            p.parent,
            {
                "model": "logistic_regression (entraîné au démarrage)",
                "features": FEATURES,
                "version": "demo",
                "metrics": metrics,
            },
        )
    return Predictor(str(p))


def predict_local(features: dict) -> dict:
    return load_predictor(MODEL_PATH).predict_one(features)


def predict_api(features: dict) -> dict:
    r = httpx.post(f"{API_URL}/predict", json=features, timeout=20)
    r.raise_for_status()
    return r.json()


def api_health() -> dict | None:
    try:
        return httpx.get(f"{API_URL}/health", timeout=5).json()
    except httpx.HTTPError:
        return None


# ---------------------------------------------------------------- Gemini
def explain_with_gemini(features: dict, result: dict) -> str:
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)
    lines = "\n".join(f"- {LABELS[k][0]} : {features[k]}" for k in FEATURES)
    prompt = (
        "Tu es un assistant pédagogique pour des étudiants en data science. "
        "Un modèle de classification entraîné sur le jeu de données Pima a estimé un risque "
        f"de diabète de {result['probability']:.0%} (niveau : {result['risk_level']}) "
        "pour les valeurs suivantes :\n"
        f"{lines}\n\n"
        "En 4 phrases maximum et en français, explique quelles variables tirent probablement "
        "cette estimation vers le haut ou vers le bas, en te basant sur les connaissances "
        "générales sur ce jeu de données. Rappelle à la fin qu'il s'agit d'un exercice "
        "pédagogique et non d'un avis médical."
    )
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text or "(réponse vide)"


# ---------------------------------------------------------------- interface
st.set_page_config(page_title="Risque de diabète", page_icon="🩺", layout="centered")
st.title("🩺 Estimation du risque de diabète")
st.caption(
    "Projet fil rouge de la formation « Déployer un modèle ML et un site web » · "
    "usage pédagogique, pas un outil médical."
)

with st.sidebar:
    st.header("Configuration")
    if API_URL:
        health = api_health()
        if health and health.get("model_loaded"):
            st.success(f"Mode API · {API_URL}")
            st.caption(f"Modèle : {health.get('model_type')} v{health.get('model_version')}")
        else:
            st.error(f"API injoignable ou sans modèle : {API_URL}")
        st.link_button("Documentation de l'API", f"{API_URL}/docs")
    else:
        st.info("Mode local : le modèle est chargé dans l'application.")
        st.caption("Définissez API_URL pour passer en mode API.")
    st.divider()
    st.subheader("Exemples")
    for name, values in EXAMPLES.items():
        if st.button(name, use_container_width=True):
            for k, v in values.items():
                st.session_state[k] = v
    if GEMINI_API_KEY:
        st.divider()
        st.caption(f"Explications Gemini activées ({GEMINI_MODEL}).")

st.subheader("Mesures du patient")
cols = st.columns(2)
features: dict[str, float] = {}
for i, key in enumerate(FEATURES):
    label, lo, hi, default, step = LABELS[key]
    st.session_state.setdefault(key, default)
    with cols[i % 2]:
        features[key] = st.slider(label, min_value=lo, max_value=hi, step=step, key=key)

if st.button("Estimer le risque", type="primary", use_container_width=True):
    try:
        result = predict_api(features) if API_URL else predict_local(features)
    except Exception as exc:  # noqa: BLE001 - on affiche l'erreur à l'utilisateur
        st.error(f"La prédiction a échoué : {exc}")
    else:
        st.session_state["last_result"] = result
        st.session_state["last_features"] = dict(features)

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    proba = result["probability"]
    level = result.get("risk_level") or risk_level(proba)
    colour = {"faible": "green", "modéré": "orange", "élevé": "red"}[level]

    st.divider()
    c1, c2 = st.columns([1, 2])
    c1.metric("Probabilité estimée", f"{proba:.0%}")
    c2.markdown(f"### Risque **:{colour}[{level}]**")
    c2.progress(min(max(proba, 0.0), 1.0))
    st.caption(
        f"Classe prédite : {result['prediction']} · modèle v{result.get('model_version', '?')} · "
        f"mode {'API' if API_URL else 'local'}"
    )

    if GEMINI_API_KEY:
        with st.expander("Expliquer cette estimation avec Gemini (Google AI Studio)"):
            if st.button("Générer l'explication"):
                with st.spinner("Gemini rédige…"):
                    try:
                        st.write(explain_with_gemini(st.session_state["last_features"], result))
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Appel Gemini impossible : {exc}")
    else:
        st.caption(
            "Astuce : définissez GEMINI_API_KEY (clé Google AI Studio) pour activer "
            "une explication en langage naturel."
        )
