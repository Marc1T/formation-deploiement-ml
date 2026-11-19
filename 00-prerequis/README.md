# Prérequis : à faire avant la séance 1

Comptez environ **1 h** pour les installations et **15 min** pour les comptes. La vérification du compte Azure for Students peut prendre de quelques heures à plusieurs jours : lancez-la en premier.

## Checklist

- [ ] Python 3.11 ou plus récent (ou laissez uv l'installer)
- [ ] uv
- [ ] Git, avec votre nom et votre e-mail configurés
- [ ] Docker Desktop (Windows : avec WSL 2 activé)
- [ ] Visual Studio Code et ses extensions Python et Docker
- [ ] Un compte GitHub, idéalement avec le GitHub Student Developer Pack
- [ ] Un compte Azure for Students (e-mail académique, sans carte bancaire)
- [ ] Un compte Google pour Google AI Studio
- [ ] Un compte Streamlit Community Cloud (connexion avec GitHub)
- [ ] Optionnel : un projet Google Cloud (voir plus bas)

## 1. Installer les outils

### uv (gestion de Python et des dépendances)

uv installe aussi Python si besoin : commencez par lui.

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Fermez puis rouvrez le terminal, puis :

```bash
uv --version
uv python install 3.11
```

### Git

- Windows : [git-scm.com/download/win](https://git-scm.com/download/win) (gardez les options par défaut, Git Bash inclus).
- macOS : `xcode-select --install` ou `brew install git`.
- Linux : `sudo apt install git` (Debian/Ubuntu).

Puis configurez votre identité, utilisée dans chaque commit :

```bash
git config --global user.name "Prénom Nom"
git config --global user.email "votre.email@universite.mg"
git config --global init.defaultBranch main
```

### Docker Desktop

Téléchargez [Docker Desktop](https://www.docker.com/products/docker-desktop/). Sur Windows, l'installeur active WSL 2 ; un redémarrage est nécessaire. Lancez Docker Desktop une première fois, puis vérifiez :

```bash
docker --version
docker run --rm hello-world
```

Si `hello-world` s'affiche, Docker fonctionne. Les machines avec peu de mémoire peuvent limiter Docker à 2 Go dans *Settings → Resources*.

### Visual Studio Code

Téléchargez [VS Code](https://code.visualstudio.com/) puis installez les extensions **Python** (Microsoft), **Docker** (Microsoft) et **GitHub Actions** (facultatif). L'extension **Jupyter** est utile pour lire les notebooks de départ.

### Vérification finale

```bash
python --version      # ou : uv run python --version
uv --version
git --version
docker --version
code --version
```

## 2. Créer les comptes

### GitHub

Créez un compte sur [github.com](https://github.com) avec votre e-mail académique (ou ajoutez-le ensuite dans *Settings → Emails*). Demandez ensuite le [GitHub Student Developer Pack](https://education.github.com/pack) : il donne accès à des crédits et à des outils gratuits pendant vos études.

### Azure for Students

1. Allez sur [azure.microsoft.com/free/students](https://azure.microsoft.com/free/students).
2. Connectez-vous avec un compte Microsoft (créez-le avec votre e-mail académique si vous n'en avez pas).
3. Vérifiez votre statut étudiant avec votre e-mail académique. Aucune carte bancaire n'est demandée.
4. Une fois validé, vous disposez de 100 $ de crédit et de services gratuits pendant 12 mois, renouvelables tant que vous êtes étudiant.

Si la vérification échoue et que le site vous propose le compte gratuit « standard » avec carte bancaire, arrêtez-vous : revenez sur la page étudiants, ou demandez de l'aide au formateur. L'offre *Azure for Students Starter* (sans crédit mais avec des services gratuits) est un repli possible.

### Google (AI Studio)

Un compte Google suffit. Connectez-vous sur [aistudio.google.com](https://aistudio.google.com) et vérifiez que vous pouvez ouvrir l'interface. La clé API sera créée pendant la séance 3. Les requêtes du palier gratuit peuvent être utilisées par Google pour améliorer ses modèles : n'y envoyez jamais de données personnelles ou confidentielles.

### Streamlit Community Cloud

Allez sur [share.streamlit.io](https://share.streamlit.io) et connectez-vous avec votre compte GitHub. Autorisez l'accès aux dépôts publics. C'est tout : le déploiement se fera en séance 3.

### Google Cloud (optionnel)

La partie Cloud Run et Vertex AI est montrée en démonstration par le formateur. Si vous voulez la pratiquer :

- l'essai gratuit de Google Cloud demande une carte bancaire pour la vérification d'identité ;
- votre enseignant peut demander des crédits via le programme *Google Cloud for Education* (Teaching credits) ; dans ce cas il vous transmettra un coupon.

## 3. Dépannage courant

| Symptôme | Cause probable | Solution |
|---|---|---|
| `uv : terme non reconnu` après l'installation | Le PATH n'est pas rechargé | Fermer et rouvrir le terminal, ou redémarrer VS Code |
| `l'exécution de scripts est désactivée` (PowerShell) | Politique d'exécution restrictive | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Docker : `WSL 2 installation is incomplete` | WSL 2 non installé | `wsl --install` dans un PowerShell administrateur, puis redémarrer |
| Docker : `error during connect` | Docker Desktop n'est pas démarré | Lancer Docker Desktop et attendre l'icône verte |
| `git push` demande un mot de passe refusé | GitHub n'accepte plus les mots de passe | Utiliser le [GitHub CLI](https://cli.github.com/) (`gh auth login`) ou un jeton d'accès personnel |
| Azure : redirigé vers un formulaire avec carte bancaire | Vérification étudiante échouée | Revenir sur la page Azure for Students, réessayer avec l'e-mail académique, sinon voir le formateur |

## 4. Pour aller plus loin avant la formation

- Relire les bases de Git : [git-scm.com/book/fr](https://git-scm.com/book/fr/v2) (chapitres 1 et 2).
- Parcourir la documentation de uv : [docs.astral.sh/uv](https://docs.astral.sh/uv/).
- Avoir sous la main un notebook à vous avec un modèle entraîné : il servira de base pour votre propre projet dès la séance 1.
