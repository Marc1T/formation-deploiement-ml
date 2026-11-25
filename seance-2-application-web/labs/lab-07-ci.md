# Lab 7 · Intégration continue avec GitHub Actions

**Durée** : 35 min · **Objectif** : à chaque push, GitHub installe le projet, régénère le modèle, lance ruff et pytest, puis construit et publie l'image de l'API dans GitHub Container Registry.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab` du lab 6, commité, et un compte GitHub. Référence : [projet-fil-rouge/.github/workflows/ci.yml](../../projet-fil-rouge/.github/workflows/ci.yml).

## ★ Parcours de base

### 1. Rendre le code conforme avant de le confier à un robot

La CI va vérifier le style avec ruff. D'une version à l'autre, ruff active par défaut des règles différentes : une CI qui passe aujourd'hui pourrait échouer demain sans que le code ait changé. On déclare donc les règles du projet. Ajoutez à `pyproject.toml` :

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I"]   # erreurs, noms inutilisés, ordre des imports
```

Puis mettez le code au propre une fois pour toutes :

```bash
uv run ruff format .
uv run ruff check --fix .
uv run ruff check . && uv run ruff format --check .
git add -A
git commit -m "Mise en forme ruff"
```

> **Point de contrôle** : `All checks passed!` et `files already formatted`.

### 2. Publier le projet sur GitHub

Créez un dépôt **public** nommé `diabete-lab` sur github.com (sans README ni `.gitignore`), puis :

```bash
git remote add origin https://github.com/<votre-compte>/diabete-lab.git
git push -u origin main
```

(Avec le GitHub CLI, une seule commande fait les deux : `gh repo create diabete-lab --public --source . --push`.)

### 3. Le problème des données

Sur la machine de GitHub, le dépôt ne contient que le pointeur `data/raw/diabetes.csv.dvc` : le CSV est dans votre remote DVC, un dossier de **votre** disque. La CI ne peut pas le lire. Pour ce lab, elle téléchargera les données publiques du jeu Pima, identiques octet pour octet (DVC vérifie l'empreinte). En séance 3 (★★), un remote sur Azure Blob et un `dvc pull` remplaceront ce téléchargement.

### 4. Le workflow

Créez `.github/workflows/ci.yml` :

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  packages: write

env:
  DATA_URL: https://raw.githubusercontent.com/Marc1T/formation-deploiement-ml/main/projet-fil-rouge/data/raw/diabetes.csv

jobs:
  qualite:
    name: Lint et tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - name: Installer Python et les dépendances
        run: uv sync --frozen
      - name: Données (le remote DVC local n'est pas accessible)
        run: curl -sSL -o data/raw/diabetes.csv "$DATA_URL"
      - name: Régénérer le modèle (nécessaire aux tests)
        run: uv run dvc repro
      - name: Ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .
      - name: Tests
        run: uv run pytest

  image:
    name: Image Docker de l'API
    needs: qualite
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - name: Régénérer le modèle
        run: |
          uv sync --frozen
          curl -sSL -o data/raw/diabetes.csv "$DATA_URL"
          uv run dvc repro
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Nom et tags de l'image (en minuscules)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/api
          tags: |
            type=raw,value=latest
            type=sha,prefix=
      - uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/api.Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

Points à remarquer :

- `uv sync --frozen` : la CI installe exactement `uv.lock` ; si le lock n'est pas à jour, elle échoue au lieu de résoudre autre chose en silence.
- `needs: qualite` : pas d'image si les tests échouent.
- `docker/metadata-action` : un nom d'image Docker doit être en minuscules. Si votre identifiant GitHub contient une majuscule, `ghcr.io/${{ github.repository }}` brut ferait échouer la construction ; l'action le convertit.

```bash
git add .github
git commit -m "CI : lint, tests, image"
git push
```

Ouvrez l'onglet **Actions** du dépôt et suivez l'exécution étape par étape.

> **Point de contrôle** : les deux jobs sont verts. Dans le journal de « Régénérer le modèle », on lit `train : accuracy=0.734` : la machine de GitHub obtient exactement votre résultat.

### 5. Faire échouer, puis réparer

Introduisez volontairement une erreur, par exemple `assert 0 <= r.json()["probability"] <= 0.5` dans `tests/test_api.py`. Poussez : le job *Lint et tests* devient rouge, le job *Image* ne démarre pas. Lisez le journal, réparez, poussez : tout redevient vert. L'erreur a été vue avant d'arriver en production.

### 6. Récupérer l'image

L'image apparaît dans l'onglet **Packages** de votre profil GitHub. Son nom complet, **en minuscules**, est `ghcr.io/<votre-compte>/diabete-lab/api`. Par défaut elle est **privée** : rendez-la publique (page du package → *Package settings* → *Change visibility* → *Public*), puis :

```bash
docker pull ghcr.io/<votre-compte-en-minuscules>/diabete-lab/api:latest
docker run --rm -d -p 8000:8000 --name api-ci ghcr.io/<votre-compte-en-minuscules>/diabete-lab/api:latest
curl http://localhost:8000/health
docker stop api-ci
```

> **Point de contrôle** : `{"status":"ok"}` : l'image construite par GitHub tourne sur votre machine. C'est elle que vous déploierez sur Azure en séance 3.

## ★★ Aller plus loin

- **Badge** dans le README : `![CI](https://github.com/<vous>/diabete-lab/actions/workflows/ci.yml/badge.svg)`.
- **Pourquoi `latest` seul est une mauvaise idée** : regardez les deux tags publiés. Lequel déploieriez-vous en production, et pourquoi ?
- **Cache Docker en CI** : `cache-from: type=gha` et `cache-to: type=gha,mode=max` dans `build-push-action`, puis comparez la durée de deux constructions.
- **Protéger `main`** : *Settings → Rules → New ruleset* : exiger une pull request et le statut *Lint et tests*. Une pull request rouge ne peut plus être fusionnée.
- **Secrets** : ajoutez un secret dans *Settings → Secrets and variables → Actions* et affichez-le dans un step : GitHub le masque dans les journaux.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `ruff format --check` échoue en CI | code non formaté | `uv run ruff format .` en local, commit, push |
| `ruff check` signale `BLE001`, `SIM115`… | règles par défaut d'une version récente de ruff | déclarer `[tool.ruff.lint] select = […]` dans `pyproject.toml` (étape 1) |
| `uv sync --frozen` : lock out of date | `uv.lock` pas commité après un `uv add` | `uv lock`, commit, push |
| `dvc repro` : `data/raw/diabetes.csv` manquant | étape de téléchargement absente ou mal placée | le `curl` doit précéder `dvc repro` |
| Les tests renvoient 503 en CI | `dvc repro` n'a pas tourné avant `pytest` | garder l'étape « Régénérer le modèle » avant les tests |
| `repository name must be lowercase` | nom d'image construit sans `metadata-action` | utiliser `docker/metadata-action`, ou un nom en minuscules |
| `denied: permission_denied` au push de l'image | `packages: write` manquant | l'ajouter dans `permissions` |
| `docker pull` : `unauthorized` | package encore privé | le rendre public, ou `docker login ghcr.io` avec un jeton `read:packages` |

## À retenir

- **La CI rejoue sur une machine neuve** ce que vous faites à la main : si ça ne marche que chez vous, elle le dit, avant la production.
- **Chaque étape conditionne la suivante** : pas d'image sans tests verts, pas de tests sans modèle régénéré.
- **La CI n'a accès qu'au dépôt et à ce qu'on lui donne** : données publiques ici, secrets ou remote cloud ensuite.
- **L'image publiée est l'artefact qu'on déploie**, avec un tag immuable (le SHA du commit) en plus de `latest`.

## Solution

Solution complète : publiée après la séance.
