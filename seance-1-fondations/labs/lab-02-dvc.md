# Lab 2 · Un pipeline reproductible avec DVC

**Durée** : 35 min · **Objectif** : découper l'entraînement en étapes décrites dans `dvc.yaml`, paramétrées par `params.yaml`, et constater que `dvc repro` ne relance que ce qui a changé.

Vous continuez dans le projet du lab 1 (ou dans une copie du fil rouge).

## ★ Parcours de base

### 1. Installer et initialiser DVC

```bash
uv add --group mlops dvc
uv run dvc init                      # (dvc init --subdir si le projet est un sous-dossier d'un dépôt Git)
git status                           # DVC a créé .dvc/ et .dvcignore
git commit -am "Initialise DVC"
```

### 2. Versionner les données

```bash
uv run dvc add data/raw/diabetes.csv
cat data/raw/diabetes.csv.dvc        # le pointeur : md5, taille, chemin
cat data/raw/.gitignore              # DVC a exclu le vrai fichier de Git
git add data/raw && git commit -m "Données brutes suivies par DVC"
```

Configurez un remote local (un dossier à côté du projet), puis poussez :

```bash
uv run dvc remote add -d local ../dvc-remote
uv run dvc push
ls ../dvc-remote/files/md5           # le contenu est rangé par hash
```

Simulation de collègue : supprimez `data/raw/diabetes.csv`, lancez `uv run dvc pull` : il revient.

### 3. Découper en étapes

Séparez votre `train.py` en deux scripts (le fil rouge montre une version plus complète dans [src/diabetes_ml](../../projet-fil-rouge/src/diabetes_ml)) :

- `prepare.py` : lit `data/raw/diabetes.csv`, remplace les 0 impossibles par NaN, découpe en `data/processed/train.csv` et `test.csv` avec `test_size` lu dans `params.yaml` ;
- `train.py` : lit `train.csv`, entraîne avec `n_estimators` et `max_depth` lus dans `params.yaml`, écrit `models/model.joblib` et `reports/metrics.json` (accuracy sur `test.csv`).

Créez `params.yaml` :

```yaml
data:
  test_size: 0.2
  random_state: 42
train:
  n_estimators: 200
  max_depth: 6
```

Lire les paramètres en Python : `yaml.safe_load(open("params.yaml"))["train"]["max_depth"]`.

### 4. Décrire le pipeline

Créez `dvc.yaml` (ou utilisez `dvc stage add`) :

```yaml
stages:
  prepare:
    cmd: python -m diabete_lab.prepare
    deps: [data/raw/diabetes.csv, src/diabete_lab/prepare.py]
    params: [data]
    outs: [data/processed/train.csv, data/processed/test.csv]
  train:
    cmd: python -m diabete_lab.train
    deps: [data/processed/train.csv, data/processed/test.csv, src/diabete_lab/train.py]
    params: [train]
    outs: [models/model.joblib]
    metrics:
      - reports/metrics.json:
          cache: false
```

Puis :

```bash
uv run dvc repro            # exécute prepare puis train
uv run dvc dag              # le graphe
uv run dvc metrics show     # accuracy
git add dvc.yaml dvc.lock params.yaml reports/metrics.json .gitignore
git commit -m "Pipeline DVC : prepare + train"
```

### 5. Constater la mise en cache

```bash
uv run dvc repro            # rien ne se relance : tout est à jour
```

Changez `max_depth: 6` en `max_depth: 10` dans `params.yaml`, puis :

```bash
uv run dvc repro            # seul train se relance : prepare est intact
uv run dvc params diff      # ce qui a changé
uv run dvc metrics diff     # l'effet sur la métrique
```

Question : que se passe-t-il si vous modifiez `test_size` ? Pourquoi les deux étapes se relancent-elles ?

## ★★ Aller plus loin

- **Expériences sans toucher aux fichiers** : `uv run dvc exp run --set-param train.max_depth=3`, puis `=12`, puis `uv run dvc exp show`. Gardez la meilleure avec `dvc exp apply <nom>`.
- **Une troisième étape** `evaluate` qui produit aussi une matrice de confusion en CSV, déclarée comme `plots` (voir [dvc.yaml](../../projet-fil-rouge/dvc.yaml) du fil rouge), puis `uv run dvc plots show`.
- **Remote cloud** : `uv add "dvc[azure]"` ; en séance 3 vous pointerez ce remote vers un conteneur Azure Blob.
- **Pourquoi `cache: false` sur les métriques ?** Cherchez dans la documentation et expliquez-le en une phrase.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `dvc init` refuse : « not a git repository » | pas de dépôt Git | `git init -b main` d'abord, ou `dvc init --no-scm` |
| `output 'models/model.joblib' is already tracked by SCM` | le fichier avait été commité dans Git | `git rm -r --cached models` puis recommencer |
| `dvc repro` ne relance rien après une modification | la dépendance modifiée n'est pas listée dans `deps` | ajoutez-la ; DVC ne surveille que ce qui est déclaré |
| Sorties « dirty » | une sortie a été modifiée à la main | `dvc repro -f` pour forcer, ou restaurer avec `dvc checkout` |

## Ce qu'il faut retenir

`dvc add` pour un fichier, `dvc.yaml` pour un pipeline, `dvc repro` pour régénérer ce qui a changé, `dvc push`/`pull` pour partager le contenu. Solution complète : publiée après la séance.
