# Comparatif des cibles de déploiement

Vérifié en **novembre 2026**. Les offres gratuites et étudiantes changent plusieurs fois par an : le formateur relit les pages de tarification la veille de la séance 3 et met à jour ce tableau.

## Pour l'application Streamlit

| Cible | Gratuit ? | Carte bancaire ? | Mise en veille | Déploiement | Notes |
|---|---|---|---|---|---|
| **Streamlit Community Cloud** | oui | non | après quelques jours sans visite | depuis un dépôt GitHub public, redéploiement à chaque push | un seul dépôt privé autorisé ; secrets dans l'interface ; ressources limitées (environ 1 Go) |
| Azure Container Apps | allocation mensuelle gratuite + crédit étudiant | non (Azure for Students) | scale-to-zero configurable | image Docker | pour une interface toujours disponible ou privée |
| Hugging Face Spaces | **Spaces Docker/Gradio devenus payants en 2026** ; Spaces statiques gratuits | | | | n'est plus retenu pour la formation ; à revérifier |

## Pour l'API conteneurisée

| Cible | Gratuit ? | Carte bancaire ? | Échelle à zéro | Construire sans Docker local | Journaux | Supprimer |
|---|---|---|---|---|---|---|
| **Azure Container Apps** | allocation mensuelle (vCPU-s, GiB-s, requêtes) + 100 $ étudiant | non avec Azure for Students | `--min-replicas 0` | `az acr build` | `az containerapp logs show` | `az group delete` |
| **Google Cloud Run** | palier gratuit mensuel ; essai 300 $ | oui pour l'essai individuel ; crédits enseignant via *Teaching credits* | `--min-instances 0` | `gcloud builds submit` | `gcloud run services logs read` | `gcloud run services delete` |
| Render (web service Docker) | plan gratuit, 750 h/mois | à vérifier à l'inscription | veille après 15 min, redémarrage 30 à 60 s | construit depuis le dépôt | tableau de bord | tableau de bord |
| Azure App Service (F1) | gratuit, limité (60 min CPU/jour) | non | veille après 20 min | déploiement de code Python, pas de conteneur sur F1 | portail | portail |

## Plateformes ML managées (démonstration)

| | Azure Machine Learning | Vertex AI |
|---|---|---|
| Console | ml.azure.com | console.cloud.google.com → Vertex AI |
| Données | Data assets, datastores | Cloud Storage, BigQuery, Feature Store |
| Exploration | Compute instance (notebooks, VS Code) | Workbench, Colab Enterprise |
| Entraînement | Jobs (script, AutoML, pipelines, designer) | Training (custom, AutoML, pipelines Kubeflow) |
| Suivi | MLflow intégré | Experiments |
| Registre | Model registry (format MLflow natif) | Model Registry |
| Déploiement | Managed online / batch endpoints | Endpoints, batch prediction |
| Supervision | Monitoring, dérive | Model Monitoring |
| IA générative | Azure AI Foundry (OpenAI, etc.) | Vertex AI Studio (Gemini) ; AI Studio pour les développeurs |
| Conteneur personnalisé | oui (environnements, endpoints) | oui (conteneur de prédiction, port `AIP_HTTP_PORT`) |
| Coût typique | calcul managé à la minute ; endpoint facturé même sans trafic | idem ; endpoint au nœud-heure |

## Programmes étudiants et enseignants

| Programme | Pour qui | Ce qu'on obtient | Où |
|---|---|---|---|
| Azure for Students | étudiants, e-mail académique | 100 $/an, services gratuits 12 mois, sans carte | azure.microsoft.com/free/students |
| Azure for Students Starter | étudiants sans crédit | services gratuits seulement | même page |
| GitHub Student Developer Pack | étudiants | crédits et outils (dont Azure, DigitalOcean…) | education.github.com/pack |
| Google Cloud Teaching credits | enseignants (domaine académique, pays éligibles) | coupons de crédits pour les étudiants d'un cours | cloud.google.com/edu |
| Google AI Studio | tout compte Google | clé Gemini, palier gratuit (limites de débit, données utilisées pour l'entraînement) | aistudio.google.com |
| Streamlit Community Cloud | tout compte GitHub | hébergement d'applications publiques | share.streamlit.io |

## Choisir en trente secondes

- **Je veux une démo publique ce soir, sans compte cloud** : Streamlit Community Cloud, mode local (repli d'entraînement ou `MODEL_URL`).
- **Je veux une vraie API, surveillée, peu chère** : Azure Container Apps (crédit étudiant) ou Cloud Run.
- **Mon équipe a plusieurs modèles, des réentraînements, des contraintes de gouvernance** : Azure ML ou Vertex AI, en déployant le même conteneur.
- **Je veux ajouter de l'IA générative** : AI Studio pour prototyper et pour un projet étudiant ; Vertex AI Studio ou Azure AI Foundry dès qu'il y a des données réelles.
