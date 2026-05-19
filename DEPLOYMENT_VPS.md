# 🚀 Guide de Déploiement pour l'Agent Gemini VPS

Bonjour collègue agent ! Tu es chargé de déployer ce bot Discord sur le VPS de l'utilisateur. Voici les étapes à suivre.

## 1. Préparation de l'environnement
Assure-tu que **Docker** et **Docker Compose** sont installés sur le système.

## 2. Récupération du code
Clone le dépôt Git (l'utilisateur te fournira l'URL si besoin) ou accède au dossier du projet.

## 3. Configuration des Secrets
Crée un fichier `.env` à la racine du projet avec le token Discord :
```bash
echo "DISCORD_BOT_TOKEN=ton_token_ici" > .env
```
*Note : Demande à l'utilisateur son token s'il ne l'a pas déjà configuré.*

## 4. Initialisation des fichiers de persistance
Docker a besoin que les fichiers mappés existent pour ne pas créer des dossiers à leur place :
```bash
touch marketplace.db
touch bot.log
```

## 5. Lancement du Bot
Exécute la commande suivante pour builder l'image et lancer le conteneur en arrière-plan :
```bash
docker compose up -d --build
```

## 6. Commandes utiles
- **Voir les logs en temps réel** : `docker compose logs -f`
- **Arrêter le bot** : `docker compose down`
- **Redémarrer le bot** : `docker compose restart`
- **Vérifier le statut** : `docker ps`

---
*Guide généré par Gemini CLI - Mode Auto-Edit*
