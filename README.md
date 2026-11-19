# Déployer un modèle ML et un site web

**De la conception du modèle à une solution en production** · Formation de la Cellule Info CEAM

Cette formation accompagne les étudiants dans la mise en production de leurs solutions : partir d'un modèle entraîné dans un notebook et arriver à une application web fonctionnelle, versionnée, conteneurisée et déployée dans le cloud. Elle présente toute la chaîne de développement et les outils qui la rendent reproductible : **uv**, **DVC**, **MLflow**, **FastAPI**, **Streamlit**, **Docker**, **GitHub Actions**, **Microsoft Azure**, **Google Cloud / Vertex AI** et **Google AI Studio**.

> Tout le matériel est en français. Les présentations sont des pages HTML animées, utilisables hors ligne. Les diagrammes sont en SVG et servent à la fois dans les slides et dans les cours.

> **Présentations en ligne** : [https://marc1t.github.io/formation-deploiement-ml/](https://marc1t.github.io/formation-deploiement-ml/) · Pour travailler sur votre machine : `git clone https://github.com/Marc1T/formation-deploiement-ml.git`

## Objectifs

À la fin de la formation, chaque étudiant sait :

1. Transformer un notebook en **projet Python reproductible** (uv, `pyproject.toml`, fichier de verrouillage).
2. **Versionner les données et le pipeline** d'entraînement avec DVC, et **tracer les expériences** avec MLflow.
3. Exposer un modèle via une **API FastAPI** et une **interface web Streamlit**, avec des tests.
4. **Conteneuriser** l'application avec Docker et automatiser les vérifications avec une **CI GitHub Actions**.
5. **Déployer** une application publique (Streamlit Community Cloud), puis une API conteneurisée sur **Azure Container Apps**.
6. Situer **Azure ML**, **Vertex AI** et **Google AI Studio** dans la chaîne, et intégrer un modèle Gemini dans une application.

## Pour qui

Étudiants de niveau hétérogène : il faut savoir écrire du Python et avoir déjà entraîné un modèle (scikit-learn ou équivalent). Git, Docker et le cloud sont introduits pendant la formation.

Chaque lab propose deux parcours :

- **★ Parcours de base** : à faire par tout le monde, guidé pas à pas.
- **★★ Aller plus loin** : pour celles et ceux qui avancent vite (pre-commit, remote DVC sur Azure Blob, déploiement continu, etc.).

## Programme : 3 séances de 3 h

| Séance | Thème | Outils | Labs |
|---|---|---|---|
| [Séance 1](seance-1-fondations/README.md) | Du notebook au projet reproductible | Git, uv, DVC, MLflow | 1 · 2 · 3 |
| [Séance 2](seance-2-application-web/README.md) | Du modèle à une application web | FastAPI, Streamlit, Docker, GitHub Actions | 4 · 5 · 6 · 7 |
| [Séance 3](seance-3-cloud/README.md) | Mise en production dans le cloud | Streamlit Cloud, Azure (Container Apps, Azure ML), GCP (Cloud Run, Vertex AI), Google AI Studio | 8 · 9 · 10 · 11 |

Variante en 2 séances : fusionner les séances 1 et 2 en gardant uv, MLflow, FastAPI et Docker ; DVC et la CI passent en lecture autonome.

## Comment utiliser ce dépôt

**Avant la séance 1**, chaque participant suit la checklist des [prérequis](00-prerequis/README.md) : installations et création des comptes (GitHub, Azure for Students, Google, Streamlit Community Cloud). La vérification du compte Azure for Students peut prendre plusieurs jours : à lancer tôt.

**Pendant une séance**, le formateur projette la présentation de la séance ; les étudiants suivent le `README.md` de cours et font les labs du dossier `labs/`. Les solutions de chaque lab sont publiées dans `labs/solutions/` après la séance correspondante.

**Le projet fil rouge** ([projet-fil-rouge/](projet-fil-rouge/README.md)) est un dépôt complet et fonctionnel : modèle, pipeline DVC, suivi MLflow, API, interface web, Docker, CI et scripts de déploiement. Il sert de référence pendant les labs et de modèle à copier pour son propre projet.

## Arborescence

```
deployment/
├── index.html                   Page d'accueil : accès aux decks, cours et fil rouge
├── 00-prerequis/                Installations et comptes à créer avant la séance 1
├── seance-1-fondations/         Cours, slides.html, labs 1 à 3
├── seance-2-application-web/    Cours, slides.html, labs 4 à 7
├── seance-3-cloud/              Cours, slides.html, labs 8 à 11
├── projet-fil-rouge/            Dépôt de démonstration complet
├── ressources/                  Comparatif cloud, checklist de mise en production, glossaire, liens
└── assets/                      Thème, animations, diagrammes SVG, reveal.js et polices inclus
```

## Outils couverts

| Outil | Rôle dans la chaîne | Séance |
|---|---|---|
| Git / GitHub | Versionner le code, collaborer, héberger la CI | 1 |
| uv | Gérer Python, les dépendances et l'environnement du projet | 1 |
| DVC | Versionner les données et rendre le pipeline reproductible | 1 |
| MLflow | Tracer les expériences, comparer les runs, enregistrer les modèles | 1 |
| FastAPI | Exposer le modèle en API REST documentée | 2 |
| Streamlit | Construire l'interface web | 2 |
| Docker | Emballer l'application pour qu'elle tourne partout | 2 |
| GitHub Actions | Tester et construire l'image automatiquement | 2 |
| Streamlit Community Cloud | Déployer gratuitement une application publique | 3 |
| Azure Container Apps, Azure ML | Héberger l'API conteneurisée ; plateforme ML managée | 3 |
| Cloud Run, Vertex AI | Équivalents Google Cloud, en démonstration | 3 |
| Google AI Studio / Gemini | Ajouter une brique d'IA générative à l'application | 3 |

## Présentations

Ouvrir `seance-X/slides.html` dans un navigateur (aucun serveur nécessaire). Raccourcis utiles :

| Touche | Action |
|---|---|
| `→` / `Espace` | Diapo ou fragment suivant |
| `S` | Vue présentateur (notes, minuteur, diapo suivante) |
| `Échap` | Vue d'ensemble |
| `D` | Basculer le thème clair / sombre |
| `F` | Plein écran |
| `?` | Liste complète des raccourcis |

Version imprimable : ouvrir `slides.html?print-pdf` dans Edge ou Chrome, puis Imprimer → Enregistrer au format PDF, en paysage.


## Licence

Contenu pédagogique diffusé sous licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.fr) ; code du projet fil rouge sous licence MIT. reveal.js est sous licence MIT (© Hakim El Hattab).
