"""
Configuration du bot Marketplace TCG.

⚙️  C'EST LE SEUL FICHIER À MODIFIER pour ajuster :
    - les TCG supportés
    - les états de carte
    - les fourchettes de prix
    - les couleurs

Pour ajouter un TCG : ajoute une entrée dans TCG_CHOICES.
Le nom du forum doit correspondre au champ "forum" ci-dessous.
"""
import os

# ── Token ──────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ── Base de données ────────────────────────────────────────
DATABASE_PATH = "marketplace.db"

# ── TCG supportés ──────────────────────────────────────────
# 'name'  : nom affiché
# 'emoji' : emoji affiché
# 'forum' : nom EXACT du forum channel Discord où router les annonces
#           (doit correspondre au script setup_marketplace_forums.py)
TCG_CHOICES = {
    "pokemon":    {"name": "Pokémon",      "emoji": "🎴", "forum": "marketplace-pokémon"},
    "onepiece":   {"name": "One Piece",    "emoji": "☠️", "forum": "marketplace-onepiece"},
    "magic":      {"name": "Magic",        "emoji": "🪄", "forum": "marketplace-magic"},
    "yugioh":     {"name": "Yu-Gi-Oh!",    "emoji": "🃏", "forum": "marketplace-yugioh"},
    "lorcana":    {"name": "Lorcana",      "emoji": "💫", "forum": "marketplace-lorcana"},
    "riftbound":  {"name": "Riftbound",    "emoji": "🔮", "forum": "marketplace-riftbound"},
    "sport":      {"name": "Cartes de Sport", "emoji": "⭐", "forum": "marketplace-sport"},
    "naruto":     {"name": "Naruto",       "emoji": "🥷", "forum": "marketplace-naruto"},
    "dragonball": {"name": "Dragon Ball",  "emoji": "🐉", "forum": "marketplace-dragonball"},
    "emergents":  {"name": "TCG Émergents","emoji": "🚀", "forum": "marketplace-autres-tcg"},
}

# ── Types d'annonce ────────────────────────────────────────
# 'label'    : nom affiché
# 'prefix'   : préfixe du titre du post
# 'tag'      : nom du tag forum à appliquer
# 'has_price': si l'annonce demande un prix
LISTING_TYPES = {
    "vente":  {"label": "Vente",  "prefix": "[VENTE]",  "tag": "Vente",  "emoji": "🛒", "has_price": True},
    "achat":  {"label": "Achat",  "prefix": "[ACHAT]",  "tag": "Achat",  "emoji": "💰", "has_price": False},
    "scelle": {"label": "Scellé", "prefix": "[SCELLÉ]", "tag": "Scellé", "emoji": "📦", "has_price": True},
}

# ── États de carte ─────────────────────────────────────────
CARD_CONDITIONS = {
    "mint":         {"name": "Mint (M)",         "emoji": "🆕", "tag": "Mint"},
    "near_mint":    {"name": "Near Mint (NM)",   "emoji": "✨", "tag": "Near Mint"},
    "excellent":    {"name": "Excellent (EX)",   "emoji": "👍", "tag": "Excellent"},
    "played":       {"name": "Played (P)",       "emoji": "📉", "tag": "Played"},
}

# ── Fourchettes de prix (pour les tags) ────────────────────
PRICE_RANGES = [
    {"min": 0,   "max": 20,     "tag": "< 20€"},
    {"min": 20,  "max": 100,    "tag": "20-100€"},
    {"min": 100, "max": 500,    "tag": "100-500€"},
    {"min": 500, "max": 1e9,    "tag": "500€+"},
]

# ── Tag de statut par défaut à la création ─────────────────
DEFAULT_STATUS_TAG = "Disponible"
SOLD_STATUS_TAG = "Vendu"

# ── Couleurs (embeds) ──────────────────────────────────────
COLORS = {
    "success":     0x2ECC71,
    "error":       0xE74C3C,
    "info":        0x3498DB,
    "marketplace": 0x9B59B6,
}

# ── Channel où poster le panneau de création d'annonce ─────
# Le bot cherche ce channel pour /setup_marketplace
CREATE_CHANNEL_NAME = "créer-annonce"
