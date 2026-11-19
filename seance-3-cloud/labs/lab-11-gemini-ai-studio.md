# Lab 11 · Gemini dans l'application avec Google AI Studio

**Durée** : 25 min · **Objectif** : ajouter une explication en langage naturel de l'estimation, générée par Gemini, sans jamais exposer la clé API.

Prérequis : un compte Google, l'application Streamlit du lab 5 (local) ou du lab 8 (Streamlit Cloud). Référence : la fonction `explain_with_gemini` de [app/streamlit_app.py](../../projet-fil-rouge/app/streamlit_app.py).

## ★ Parcours de base

### 1. Prototyper dans AI Studio

Sur [aistudio.google.com](https://aistudio.google.com), nouveau prompt. Collez :

> Tu es un assistant pédagogique pour des étudiants en data science. Un modèle entraîné sur le jeu de données Pima a estimé un risque de diabète de 72 % pour : glycémie 175 mg/dL, IMC 36,8, âge 52, 6 grossesses, antécédents familiaux 1,1. En quatre phrases maximum et en français, explique quelles variables tirent probablement cette estimation vers le haut, puis rappelle qu'il s'agit d'un exercice pédagogique et non d'un avis médical.

Ajustez jusqu'à obtenir le ton voulu. Notez le modèle utilisé (par exemple `gemini-2.5-flash`). L'interface montre aussi le code équivalent (*Get code*).

### 2. Créer une clé

*Get API key → Create API key*. Copiez-la. Elle ne doit jamais apparaître dans un fichier commité : si cela arrive, revenez ici, supprimez-la, recréez-en une.

### 3. La ranger dans un secret

En local, dans `.env` (ignoré par Git) :

```
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.5-flash
```

Sur Streamlit Cloud : *Manage app → Settings → Secrets*, les mêmes deux lignes au format TOML (`GEMINI_API_KEY = "AIza..."`).

### 4. L'appeler depuis l'application

```bash
uv add --group app google-genai
```

Dans `app/streamlit_app.py` :

```python
import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def explain_with_gemini(features: dict, result: dict) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    lines = "\n".join(f"- {k} : {v}" for k, v in features.items())
    prompt = (
        "Tu es un assistant pédagogique pour des étudiants en data science. "
        f"Un modèle a estimé un risque de diabète de {result['probability']:.0%} pour :\n{lines}\n\n"
        "En quatre phrases maximum et en français, explique quelles variables tirent probablement "
        "cette estimation vers le haut ou vers le bas. Rappelle à la fin qu'il s'agit d'un exercice "
        "pédagogique et non d'un avis médical."
    )
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text or "(réponse vide)"


# après l'affichage du résultat :
if GEMINI_API_KEY and st.button("Expliquer cette estimation"):
    with st.spinner("Gemini rédige…"):
        try:
            st.write(explain_with_gemini(features, result))
        except Exception as exc:
            st.error(f"Appel Gemini impossible : {exc}")
```

Sans clé, le bouton n'apparaît pas : l'application reste utilisable.

### 5. Tester, puis observer les limites

Lancez l'application, faites une estimation, cliquez. Puis cliquez dix fois de suite rapidement : le palier gratuit limite le nombre de requêtes par minute ; l'erreur `429 RESOURCE_EXHAUSTED` apparaît dans votre `st.error`, pas dans une page blanche. Les limites exactes sont affichées dans AI Studio et changent régulièrement.

### 6. Vérifier qu'aucune clé n'est dans Git

```bash
git grep -n "AIza"            # ne doit rien trouver
git status                    # .env ne doit pas apparaître
```

## ★★ Aller plus loin

- **Déplacer l'appel côté API** : une route `POST /explain` dans FastAPI, la clé en secret Container Apps (`az containerapp secret set` puis `--env-vars GEMINI_API_KEY=secretref:gemini`). L'interface n'a plus la clé du tout. Quel avantage ? Quel inconvénient ?
- **Sortie structurée** : demandez à Gemini un JSON `{"facteurs": [...], "conseil": "..."}` avec `response_mime_type="application/json"` dans `config`, et affichez-le proprement.
- **Mise en cache** : `@st.cache_data` sur l'explication (clé = les mesures) pour ne pas rappeler Gemini pour les mêmes valeurs.
- **Vertex AI Studio** : la même API Gemini existe dans Google Cloud, facturée et gouvernée par le projet ; pour une entreprise, c'est là que la clé AI Studio est remplacée par un compte de service.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `API key not valid` | clé mal copiée, ou restreinte | recréer une clé dans AI Studio |
| `429 RESOURCE_EXHAUSTED` | limite du palier gratuit | attendre une minute ; mettre en cache |
| `404 model not found` | nom de modèle obsolète | vérifier la liste des modèles dans AI Studio et `GEMINI_MODEL` |
| Le bouton n'apparaît pas | `GEMINI_API_KEY` vide | `.env` chargé ? secret enregistré sur Streamlit Cloud ? |

## Ce qu'il faut retenir

Prototyper dans AI Studio, ranger la clé dans un secret, appeler le SDK depuis le code, gérer les erreurs et les limites. Et ne jamais envoyer de données personnelles au palier gratuit. Solution : publiée après la séance.
