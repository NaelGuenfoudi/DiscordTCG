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

import config
from cogs.views import ListingActionsView, PanelView

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
