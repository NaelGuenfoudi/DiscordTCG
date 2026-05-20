"""
Bot Marketplace TCG — point d'entrée.

Lancement :
    export DISCORD_BOT_TOKEN="ton_token"
    python main.py
"""
import asyncio
import logging
import sys

import discord
from discord.ext import commands

from discord import app_commands
import config
from cogs import embeds
from cogs.views import ListingActionsView, PanelView
from database.models import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("marketplace")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    log.info("Connecté : %s", bot.user)
    for guild in bot.guilds:
        log.info("  Serveur : %s (%s)", guild.name, guild.id)

    # Vues persistantes (les boutons survivent à un redémarrage)
    bot.add_view(PanelView())
    bot.add_view(ListingActionsView())

    try:
        synced = await bot.tree.sync()
        log.info("Commandes slash synchronisées : %d", len(synced))
    except Exception as e:  # noqa: BLE001
        log.error("Échec sync commandes : %s", e)

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="la marketplace TCG",
        )
    )
    log.info("Bot prêt.")


# ── Commandes Profil ───────────────────────────────────────

async def _show_profile(interaction: discord.Interaction, user: discord.User | discord.Member):
    """Logique commune pour afficher le profil."""
    # On diffère la réponse immédiatement pour éviter le timeout de 3s
    await interaction.response.defer(ephemeral=True)
    
    profile = db.get_user_profile(str(user.id))
    if not profile:
        # Créer un profil vide si l'utilisateur n'existe pas encore en BDD
        db.get_or_create_user(str(user.id), user.display_name)
        profile = db.get_user_profile(str(user.id))

    from cogs.views import ProfileShareView
    embed = embeds.build_profile_embed(user, profile)
    view = ProfileShareView(user, profile)
    
    # On utilise followup.send car on a déjà fait un defer()
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="profil", description="Affiche le profil marketplace d'un utilisateur")
@app_commands.describe(membre="Le membre dont tu veux voir le profil")
async def profil(interaction: discord.Interaction, membre: discord.User = None):
    target = membre or interaction.user
    await _show_profile(interaction, target)


# Commande clic-droit (Context Menu) - Toujours éphémère
@bot.tree.context_menu(name="Voir le profil TCG")
async def profil_context(interaction: discord.Interaction, user: discord.Member):
    await _show_profile(interaction, user)


async def main():
    if not config.DISCORD_TOKEN:
        log.error("DISCORD_BOT_TOKEN manquant. Définis la variable d'environnement.")
        sys.exit(1)

    async with bot:
        await bot.load_extension("cogs.marketplace")
        log.info("Cog chargé : cogs.marketplace")
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Arrêt manuel.")
