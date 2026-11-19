# Lab 7 · Intégration continue avec GitHub Actions

**Durée** : 30 min · **Objectif** : à chaque push, GitHub installe le projet, lance ruff et pytest, puis construit et publie l'image de l'API dans GitHub Container Registry.

Référence : [projet-fil-rouge/.github/workflows/ci.yml](../../projet-fil-rouge/.github/workflows/ci.yml). Il vous faut un compte GitHub et votre projet poussé dans un dépôt.

## ★ Parcours de base

### 1. Le workflow minimal : qualité

Créez `.github/workflows/ci.yml` :

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  qualite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv python install
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest
```

Commitez, poussez, ouvrez l'onglet **Actions** du dépôt. Suivez l'exécution étape par étape.

### 2. Faire échouer, puis réparer

Introduisez volontairement une erreur (un test faux, ou une ligne trop longue), poussez, observez la croix rouge et le journal. Réparez, poussez : coche verte. C'est tout l'intérêt : l'erreur est vue avant d'arriver en production.

### 3. Construire et publier l'image

Ajoutez un second job, qui ne tourne que si le premier réussit :

```yaml
permissions:
  contents: read
  packages: write

jobs:
  qualite:
    # … inchangé …

  image:
    needs: qualite
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv python install && uv sync --frozen && uv run dvc repro
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/api.Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository }}/api:latest
```

Poussez. À la fin, l'image apparaît dans l'onglet **Packages** de votre profil (ou du dépôt). Notez son nom complet : `ghcr.io/<vous>/<depot>/api:latest`. C'est ce nom que vous donnerez à Azure en séance 3.

### 4. Récupérer l'image depuis votre machine

Par défaut le package est **privé**. Deux options :

- le rendre public : page du package → *Package settings* → *Change visibility* ;
- ou vous authentifier : `echo <PAT> | docker login ghcr.io -u <vous> --password-stdin` avec un jeton personnel ayant le droit `read:packages`.

Puis :

```bash
docker pull ghcr.io/<vous>/<depot>/api:latest
docker run --rm -p 8000:8000 ghcr.io/<vous>/<depot>/api:latest
```

L'API construite par GitHub tourne sur votre machine : même image partout.

## ★★ Aller plus loin

- **Badge** dans le README : `![CI](https://github.com/<vous>/<depot>/actions/workflows/ci.yml/badge.svg)`.
- **Tags d'image** : `docker/metadata-action@v5` pour taguer avec le SHA du commit et la version (voir le fil rouge). Pourquoi `latest` seul est-il une mauvaise idée en production ?
- **Cache Docker en CI** : `cache-from: type=gha` / `cache-to: type=gha,mode=max` dans `build-push-action`.
- **Protéger `main`** : *Settings → Branches → Require status checks* : impossible de fusionner une pull request dont la CI est rouge.
- **Secrets** : ajoutez un secret bidon dans *Settings → Secrets and variables → Actions* et affichez-le dans un step : GitHub le masque dans les journaux.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `uv sync --frozen` : lock out of date | `uv.lock` pas commité après un `uv add` | `uv lock`, commit, push |
| `denied: permission_denied` au push de l'image | `permissions: packages: write` manquant | l'ajouter au niveau du workflow ou du job |
| `dvc repro` échoue en CI | fichier de données absent (gitignoré) | commiter les petites données, ou `dvc pull` depuis un remote |
| Le job `image` ne se lance pas | `needs: qualite` et le job qualité a échoué, ou c'est une pull request | lire le journal du premier job |

## Ce qu'il faut retenir

La CI rejoue sur une machine neuve ce que vous faites à la main ; si ça ne marche que chez vous, elle le dit. L'image publiée est l'artefact que le cloud déploiera. Solution complète : publiée après la séance.
