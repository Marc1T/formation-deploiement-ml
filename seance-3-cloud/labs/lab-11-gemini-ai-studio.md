# Lab 11 · Gemini dans l'application avec Google AI Studio

**Durée** : 25 min · **Objectif** : ajouter une explication en langage naturel de l'estimation, générée par Gemini, sans jamais exposer la clé API, en local comme sur Streamlit Cloud.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : l'application du lab 8, avec sa fonction `setting`, et un compte Google. Référence : la fonction `explain_with_gemini` de [app/streamlit_app.py](../../projet-fil-rouge/app/streamlit_app.py).

## ★ Parcours de base

### 1. Prototyper dans AI Studio

Sur [aistudio.google.com](https://aistudio.google.com), ouvrez un nouveau prompt et collez :

> Tu es un assistant pédagogique pour des étudiants en data science. Un modèle entraîné sur le jeu de données Pima a estimé un risque de diabète de 58 % pour : glycémie 138 mg/dL, IMC 33,6, âge 45, 2 grossesses, antécédents familiaux 0,62. En quatre phrases maximum et en français, explique quelles variables tirent probablement cette estimation vers le haut, puis rappelle qu'il s'agit d'un exercice pédagogique et non d'un avis médical.

Ajustez jusqu'à obtenir le ton voulu. Notez le nom du modèle utilisé, affiché dans le panneau de droite ou dans *Get code*.

### 2. Créer une clé

*Get API key* → *Create API key*. Copiez-la. Elle ne doit jamais apparaître dans un fichier commité : si cela arrive, revenez ici, supprimez-la, recréez-en une.

### 3. La ranger dans un secret

En local, ajoutez à `.env` (ignoré par Git depuis le lab 1) :

```
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-flash-latest
```

`gemini-flash-latest` désigne toujours le modèle Flash le plus récent. Si AI Studio affiche un autre nom à l'étape 1, vous pouvez le mettre à la place.

### 4. L'appeler depuis l'application

```bash
uv add --group app google-genai
```

Dans `app/streamlit_app.py`, sous `DATA_URL = …`, ajoutez :

```python
GEMINI_API_KEY = setting("GEMINI_API_KEY")
GEMINI_MODEL = setting("GEMINI_MODEL", "gemini-flash-latest")


def explain_with_gemini(values: dict, result: dict) -> str:
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)
    lines = "\n".join(f"- {k} : {v}" for k, v in values.items())
    prompt = (
        "Tu es un assistant pédagogique pour des étudiants en data science. "
        f"Un modèle a estimé un risque de diabète de {result['probability']:.0%} pour :\n{lines}\n\n"
        "En quatre phrases maximum et en français, explique quelles variables tirent probablement "
        "cette estimation vers le haut ou vers le bas. Rappelle à la fin qu'il s'agit d'un exercice "
        "pédagogique et non d'un avis médical."
    )
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text or "(réponse vide)"
```

Puis, **à la fin** du bloc `if "result" in st.session_state:` (même indentation que `st.metric`) :

```python
    if GEMINI_API_KEY and st.button("Expliquer cette estimation"):
        with st.spinner("Gemini rédige…"):
            try:
                st.write(explain_with_gemini(st.session_state["values"], result))
            except Exception as exc:
                st.error(f"Appel Gemini impossible : {exc}")
```

Pourquoi à cet endroit ? Un clic sur le second bouton réexécute tout le script : le premier bouton vaut alors `False`. C'est `st.session_state` qui garde le résultat affiché, et donc le second bouton. Un bouton placé sous `if st.button("Estimer le risque")` n'aurait jamais d'effet.

Sans clé, le bouton n'apparaît pas : l'application reste utilisable.

### 5. Tester en local, puis observer les erreurs

```bash
uv run streamlit run app/streamlit_app.py
```

Estimez, puis cliquez sur **Expliquer cette estimation**.

> **Point de contrôle** : quatre phrases en français s'affichent, terminées par le rappel « exercice pédagogique ».

Remplacez la clé de `.env` par `AIzaFAUSSE`, relancez, cliquez : un message `Appel Gemini impossible : 400 … API key not valid` s'affiche, l'application continue de fonctionner. Remettez la vraie clé. Cliquez ensuite dix fois de suite : selon les limites du jour de l'offre gratuite, une erreur `429 RESOURCE_EXHAUSTED` peut apparaître, elle aussi proprement.

### 6. Déployer sur Streamlit Cloud

La bibliothèque `google-genai` est nouvelle : régénérez le fichier de dépendances de Streamlit Cloud, sinon le déploiement échouera à l'import.

```bash
uv export --format requirements-txt --no-default-groups --group app --no-hashes --no-emit-project -o app/requirements.txt
grep google-genai app/requirements.txt
git grep -n "AIza" || echo "aucune clé dans le dépôt"
git status --short            # .env ne doit pas apparaître
git add -A
git commit -m "Explication par Gemini"
git push
```

Sur Streamlit Cloud → **Settings** → **Secrets**, ajoutez sous `API_URL` :

```toml
GEMINI_API_KEY = "AIza..."
GEMINI_MODEL = "gemini-flash-latest"
```

> **Point de contrôle** : l'application en ligne affiche le bouton et l'explication ; `git grep` ne trouve aucune clé.

## ★★ Aller plus loin

- **Déplacer l'appel côté API** : une route `POST /explain` dans FastAPI, la clé en secret Container Apps (`az containerapp secret set --secrets gemini=AIza...` puis `--set-env-vars GEMINI_API_KEY=secretref:gemini`). L'interface n'a plus du tout la clé. Quel avantage, quel inconvénient ?
- **Sortie structurée** : demandez un JSON `{"facteurs": [...], "conseil": "..."}` avec `config=types.GenerateContentConfig(response_mime_type="application/json")` et affichez-le proprement.
- **Mise en cache** : `@st.cache_data` sur l'explication, avec les mesures comme clé, pour ne pas rappeler Gemini pour les mêmes valeurs.
- **Vertex AI Studio** : la même API Gemini existe dans Google Cloud, facturée et gouvernée par le projet ; en entreprise, la clé AI Studio y est remplacée par un compte de service.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `400 … API key not valid` | clé mal copiée, ou supprimée | recréer une clé dans AI Studio |
| `429 RESOURCE_EXHAUSTED` | limite de l'offre gratuite | attendre une minute ; mettre en cache |
| `404 … model not found` | nom de modèle inconnu | copier le nom exact affiché dans AI Studio dans `GEMINI_MODEL` |
| Le bouton n'apparaît pas | `GEMINI_API_KEY` vide | `.env` présent et relu (relancer Streamlit) ; secret enregistré sur Streamlit Cloud |
| Le bouton n'a aucun effet | placé sous le bouton « Estimer » | le mettre dans le bloc `if "result" in st.session_state:` |
| `ModuleNotFoundError: google` sur Streamlit Cloud | `app/requirements.txt` non régénéré | relancer `uv export`, commit, push |

## À retenir

- **Prototyper dans AI Studio, appeler par le SDK** : le prompt se met au point dans l'interface, puis se copie dans le code.
- **La clé est un secret** : `.env` en local, *Secrets* sur la plateforme, jamais dans le dépôt ; une clé commitée se révoque.
- **Tout appel à un service externe peut échouer** : clé invalide, quota, panne ; l'application doit le dire et continuer.
- **Pas de données personnelles sur l'offre gratuite** : Google peut utiliser ces requêtes pour améliorer ses modèles.

## Solution

Solution complète : publiée après la séance.
