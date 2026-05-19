"""
Cog Marketplace : commande admin pour poser le panneau de création.
"""
import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs import embeds
from cogs.views import PanelView


class Marketplace(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setup_marketplace",
        description="[Admin] Pose le panneau de création d'annonce dans ce salon.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_marketplace(self, interaction: discord.Interaction):
        await interaction.channel.send(
            embed=embeds.build_panel_embed(),
            view=PanelView(),
        )
        await interaction.response.send_message(
            "✅ Panneau de création d'annonce posé.",
            ephemeral=True,
        )

    @setup_marketplace.error
    async def _setup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Réservé aux administrateurs.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Marketplace(bot))
