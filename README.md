# 🛒 Bot Marketplace TCG

Bot Discord — marketplace par TCG avec interface 100% cliquable.

## Installation

```bash
pip install -r requirements.txt
export DISCORD_BOT_TOKEN="ton_token"     # Windows : $env:DISCORD_BOT_TOKEN="..."
python main.py
```

Puis sur Discord, dans le salon `créer-annonce` :
```
/setup_marketplace
```

## Pré-requis Discord

- Intents activés : **SERVER MEMBERS** + **MESSAGE CONTENT**
- Permissions bot : **Gérer les salons**, **Gérer les fils**, **Envoyer des messages**, **Intégrer des liens**
- Les forums marketplace créés (script `setup_marketplace_forums.py`)

## Structure

```
marketplace_bot/
├── main.py              Point d'entrée
├── config.py            ⚙️ TOUT se configure ici (TCG, états, prix...)
├── requirements.txt
├── cogs/
│   ├── marketplace.py   Commande /setup_marketplace
│   ├── views.py         Boutons, menus, modales (flux de création)
│   ├── embeds.py        Construction des embeds / titres
│   └── routing.py       Routage vers forums + tags
└── database/
    └── models.py        SQLite (users, listings...)
```

## Modifier le bot

| Pour... | Fichier |
|---|---|
| Ajouter / retirer un TCG | `config.py` → `TCG_CHOICES` |
| Changer les états de carte | `config.py` → `CARD_CONDITIONS` |
| Changer les fourchettes de prix | `config.py` → `PRICE_RANGES` |
| Modifier le flux (étapes) | `cogs/views.py` |
| Modifier l'apparence des annonces | `cogs/embeds.py` |
| Modifier le routage / tags | `cogs/routing.py` |

⚠️ Si tu ajoutes un TCG dans `config.py`, crée aussi le forum Discord
correspondant (champ `forum`).

## Fonctionnement

1. Membre clique **Vendre / Acheter / Scellé** sur le panneau
2. Choix du TCG → formulaire → état → photo → récap
3. Le bot publie dans le forum du TCG, avec tags auto
4. Sur le post : bouton **Contacter** + **Marquer comme vendu**
