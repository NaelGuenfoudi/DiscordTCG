#!/usr/bin/env python3
"""
Script de setup de la MARKETPLACE — 1 forum par TCG.

Crée :
- La catégorie 🛒 MARKETPLACE
- Un Forum Channel par TCG (Pokémon, One Piece, Magic, Yu-Gi-Oh!,
  Lorcana, Riftbound, Sport, Naruto, Dragon Ball, TCG Émergents)
- Les tags sur chaque forum (type d'annonce, prix, état, statut)

⚠️  Ce script SUPPRIME aussi les anciens channels marketplace
    (ventes-cartes, achats-cartes, trades, ventes-sealed, et les
    vieux channels achat/vente par TCG) — voir CLEANUP_CHANNELS.
    Mets DRY_RUN = True pour voir ce qui serait supprimé sans rien casser.

Usage:
    export DISCORD_BOT_TOKEN="ton_token"
    python setup_marketplace_forums.py
"""
import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════

# Si True : affiche ce qui serait supprimé/créé SANS rien modifier.
# Mets True pour un premier test, puis False pour exécuter réellement.
DRY_RUN = False

CATEGORY_NAME = "🛒 MARKETPLACE"

# Les TCG → un forum par entrée
# 'key' = identifiant interne (utilisé aussi par le bot, à garder cohérent)
# 'channel' = nom du channel Discord
# 'emoji' = emoji affiché
TCG_FORUMS = [
    {"key": "pokemon",    "channel": "marketplace-pokémon",    "emoji": "🎴", "label": "Pokémon"},
    {"key": "onepiece",   "channel": "marketplace-onepiece",   "emoji": "☠️", "label": "One Piece"},
    {"key": "magic",      "channel": "marketplace-magic",      "emoji": "🪄", "label": "Magic"},
    {"key": "yugioh",     "channel": "marketplace-yugioh",     "emoji": "🃏", "label": "Yu-Gi-Oh!"},
    {"key": "lorcana",    "channel": "marketplace-lorcana",    "emoji": "💫", "label": "Lorcana"},
    {"key": "riftbound",  "channel": "marketplace-riftbound",  "emoji": "🔮", "label": "Riftbound"},
    {"key": "sport",      "channel": "marketplace-sport",      "emoji": "⭐", "label": "Cartes de Sport"},
    {"key": "naruto",     "channel": "marketplace-naruto",     "emoji": "🥷", "label": "Naruto"},
    {"key": "dragonball", "channel": "marketplace-dragonball", "emoji": "🐉", "label": "Dragon Ball"},
    {"key": "emergents",  "channel": "marketplace-autres-tcg", "emoji": "🚀", "label": "TCG Émergents"},
]

# Tags appliqués à CHAQUE forum marketplace
MARKETPLACE_TAGS = [
    # Type d'annonce
    {"name": "Vente",        "emoji": "🛒"},
    {"name": "Achat",        "emoji": "💰"},
    {"name": "Scellé",       "emoji": "📦"},
    # Fourchette de prix
    {"name": "< 20€",        "emoji": "💸"},
    {"name": "20-100€",      "emoji": "💵"},
    {"name": "100-500€",     "emoji": "💎"},
    {"name": "500€+",        "emoji": "🏆"},
    # État
    {"name": "Mint",         "emoji": "🆕"},
    {"name": "Near Mint",    "emoji": "✨"},
    {"name": "Excellent",    "emoji": "👍"},
    {"name": "Played",       "emoji": "📉"},
    # Statut
    {"name": "Disponible",   "emoji": "🟢"},
    {"name": "En négo",      "emoji": "🟡"},
    {"name": "Vendu",        "emoji": "🔴"},
]

# Anciens channels marketplace à SUPPRIMER (cleanup)
# Le script cherche tout channel dont le nom contient un de ces termes.
CLEANUP_KEYWORDS = [
    "vente-carte", "ventes-carte", "vente-cartes", "ventes-cartes",
    "achat-carte", "achats-carte", "achat-cartes", "achats-cartes",
    "vente-item", "ventes-item", "vente-items", "ventes-items",
    "achat-item", "achats-item", "achat-items", "achats-items",
    "ventes-sealed", "vente-sealed", "achats-sealed", "achat-sealed",
    "trades", "trade",
]


# ════════════════════════════════════════════════════════════
# SCRIPT
# ════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    
    if not bot.guilds:
        print("❌ Le bot n'est sur aucun serveur !")
        await bot.close()
        return
    
    guild = bot.guilds[0]
    print(f"📍 Serveur : {guild.name}")
    
    if DRY_RUN:
        print("\n⚠️  MODE DRY_RUN ACTIVÉ — rien ne sera modifié.")
        print("    Passe DRY_RUN = False dans le script pour exécuter réellement.\n")
    else:
        print("\n🔴 MODE RÉEL — les modifications vont être appliquées.\n")
    
    if not guild.me.guild_permissions.manage_channels:
        print("❌ Le bot n'a pas la permission 'Gérer les salons' !")
        await bot.close()
        return
    
    # ────────────────────────────────────────────────────────
    # ÉTAPE 1 — CLEANUP des anciens channels
    # ────────────────────────────────────────────────────────
    print("🧹 ÉTAPE 1 — Suppression des anciens channels marketplace\n")
    
    to_delete = []
    for channel in guild.channels:
        name_lower = channel.name.lower()
        for keyword in CLEANUP_KEYWORDS:
            if keyword in name_lower:
                to_delete.append(channel)
                break
    
    if not to_delete:
        print("  ✓ Aucun ancien channel à supprimer.\n")
    else:
        for channel in to_delete:
            if DRY_RUN:
                print(f"  [DRY_RUN] Serait supprimé : #{channel.name}")
            else:
                try:
                    await channel.delete(reason="Cleanup marketplace - migration vers forums par TCG")
                    print(f"  🗑️  Supprimé : #{channel.name}")
                    await asyncio.sleep(0.7)
                except Exception as e:
                    print(f"  ❌ Erreur suppression #{channel.name} : {e}")
        print()
    
    # ────────────────────────────────────────────────────────
    # ÉTAPE 2 — CRÉATION de la catégorie
    # ────────────────────────────────────────────────────────
    print("📁 ÉTAPE 2 — Catégorie MARKETPLACE\n")
    
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    
    if category:
        print(f"  ⏭️  Catégorie déjà existante : {CATEGORY_NAME}\n")
    elif DRY_RUN:
        print(f"  [DRY_RUN] Serait créée : {CATEGORY_NAME}\n")
        category = None
    else:
        category = await guild.create_category(CATEGORY_NAME)
        print(f"  ✅ Catégorie créée : {CATEGORY_NAME}\n")
        await asyncio.sleep(0.5)
    
    # ────────────────────────────────────────────────────────
    # ÉTAPE 3 — CRÉATION des forums par TCG
    # ────────────────────────────────────────────────────────
    print("🗂️  ÉTAPE 3 — Forums marketplace par TCG\n")
    
    created = 0
    skipped = 0
    
    for tcg in TCG_FORUMS:
        existing = discord.utils.get(guild.channels, name=tcg["channel"])
        
        if existing:
            print(f"  ⏭️  Déjà existant : #{tcg['channel']}")
            skipped += 1
            continue
        
        if DRY_RUN:
            print(f"  [DRY_RUN] Serait créé : #{tcg['channel']} ({len(MARKETPLACE_TAGS)} tags)")
            continue
        
        try:
            # Préparer les tags
            tags = []
            for tag_data in MARKETPLACE_TAGS:
                try:
                    tags.append(discord.ForumTag(
                        name=tag_data["name"],
                        emoji=discord.PartialEmoji(name=tag_data["emoji"]),
                    ))
                except Exception as e:
                    print(f"     ⚠️  Tag {tag_data['name']} ignoré : {e}")
            
            forum = await guild.create_forum(
                name=tcg["channel"],
                topic=f"Marketplace {tcg['label']} — vente, achat et sealed. Utilise les tags pour filtrer.",
                category=category,
                available_tags=tags,
                default_layout=discord.ForumLayoutType.list_view,
            )
            print(f"  ✅ Créé : #{tcg['channel']} ({len(tags)} tags)")
            created += 1
            await asyncio.sleep(1.0)
        except discord.Forbidden:
            print(f"  ❌ Permission refusée : #{tcg['channel']}")
        except Exception as e:
            print(f"  ❌ Erreur création #{tcg['channel']} : {e}")
    
    # ────────────────────────────────────────────────────────
    # RÉCAPITULATIF
    # ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if DRY_RUN:
        print("🔍 DRY_RUN TERMINÉ — aucune modification effectuée")
        print("=" * 60)
        print("\n💡 Pour exécuter réellement :")
        print("   1. Ouvre setup_marketplace_forums.py")
        print("   2. Change 'DRY_RUN = True' en 'DRY_RUN = False'")
        print("   3. Relance le script")
    else:
        print("🎉 SETUP MARKETPLACE TERMINÉ !")
        print("=" * 60)
        print(f"\n📊 Résumé :")
        print(f"  • Anciens channels supprimés : {len(to_delete)}")
        print(f"  • Forums créés : {created}")
        print(f"  • Forums déjà existants : {skipped}")
        print(f"\n💡 Prochaine étape :")
        print(f"  1. (Optionnel) Coche 'Demander des tags' dans chaque forum")
        print(f"  2. Déploie le bot marketplace")
        print(f"  3. Lance /setup_marketplace dans #créer-annonce")
    
    print(f"\n🛑 Déconnexion du bot.")
    await bot.close()


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    
    if not token:
        print("❌ ERREUR : variable DISCORD_BOT_TOKEN non définie\n")
        print("  Windows : $env:DISCORD_BOT_TOKEN='ton_token'")
        print("  Mac/Linux : export DISCORD_BOT_TOKEN='ton_token'")
        print("  Puis : python setup_marketplace_forums.py")
        exit(1)
    
    print("=" * 60)
    print("🛒 SETUP MARKETPLACE FORUMS - TCG Community")
    print("=" * 60)
    print("\n🚀 Lancement...\n")
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("\n❌ Token invalide")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")