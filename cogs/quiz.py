import re
import unicodedata
import discord
from discord import app_commands, ui
from discord.ext import commands

def normalize_text(text: str) -> str:
    """Nettoyage : minuscule, sans accent, garde les espaces simples."""
    text = unicodedata.normalize('NFD', text)
    text = "".join([c for c in text if unicodedata.category(c) != 'Mn'])
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_quiz_staff():
    """Vérifie si l'utilisateur est admin ou possède un rôle Staff/Animateur."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        
        allowed_roles = {"staff", "animateur"}
        user_role_names = {role.name.lower() for role in interaction.user.roles}
        return not allowed_roles.isdisjoint(user_role_names)
    
    return app_commands.check(predicate)

class QuizLoadModal(ui.Modal, title="Chargement du Quiz"):
    reponses = ui.TextInput(
        label="Réponses (une par ligne)",
        style=discord.TextStyle.paragraph,
        placeholder="Exemple:\nChen / Prof Chen\nDracaufeu\nMetang",
        required=True
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        raw_lines = self.reponses.value.split('\n')
        self.cog.answers = [line.strip() for line in raw_lines if line.strip()]
        
        if not self.cog.answers:
            await interaction.response.send_message("❌ Aucune réponse détectée.", ephemeral=True)
            return

        self.cog.current_idx = -1
        self.cog.scores = {}
        self.cog.last_winner_id = None
        self.cog.is_listening = False
        
        await interaction.response.send_message(
            f"✅ J'ai bien reçu tes {len(self.cog.answers)} réponses. Le quiz est prêt !\nUtilise `/next` pour lancer la première question.",
            ephemeral=True
        )

class Quiz(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.answers = []
        self.current_idx = -1
        self.scores = {}
        self.last_winner_id = None # Pour la commande de correction
        self.is_listening = False
        self.quiz_channel_id = None

    async def set_channel_lock(self, channel: discord.TextChannel, locked: bool):
        overwrite = channel.overwrites_for(channel.guild.default_role)
        overwrite.send_messages = False if locked else None
        await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)

    @app_commands.command(name="lock", description="[Staff] Verrouille le salon.")
    @is_quiz_staff()
    async def lock(self, interaction: discord.Interaction):
        await self.set_channel_lock(interaction.channel, True)
        await interaction.response.send_message("🔒 Salon verrouillé.", ephemeral=False)

    @app_commands.command(name="unlock", description="[Staff] Déverrouille le salon.")
    @is_quiz_staff()
    async def unlock(self, interaction: discord.Interaction):
        await self.set_channel_lock(interaction.channel, False)
        await interaction.response.send_message("🔓 Salon déverrouillé.", ephemeral=False)

    @app_commands.command(name="quiz_load", description="[Staff] Charger les réponses.")
    @is_quiz_staff()
    async def quiz_load(self, interaction: discord.Interaction):
        await interaction.response.send_modal(QuizLoadModal(self))

    @app_commands.command(name="quiz_reponses", description="[Staff] Liste les réponses.")
    @is_quiz_staff()
    async def quiz_reponses(self, interaction: discord.Interaction):
        if not self.answers:
            await interaction.response.send_message("❌ Aucune réponse chargée.", ephemeral=True)
            return
        reponses_str = "\n".join([f"{i+1}- {resp}" for i, resp in enumerate(self.answers)])
        await interaction.response.send_message(f"📋 **Réponses :**\n{reponses_str}", ephemeral=True)

    @app_commands.command(name="quiz_force_winner", description="[Staff] Change le gagnant de la dernière question.")
    @app_commands.describe(membre="Le membre qui aurait dû gagner")
    @is_quiz_staff()
    async def quiz_force_winner(self, interaction: discord.Interaction, membre: discord.Member):
        if self.last_winner_id is None:
            await interaction.response.send_message("❌ Impossible de trouver le dernier gagnant.", ephemeral=True)
            return

        # On retire le point à l'ancien
        if self.last_winner_id in self.scores:
            self.scores[self.last_winner_id] = max(0, self.scores[self.last_winner_id] - 1)
        
        # On donne le point au nouveau
        self.scores[membre.id] = self.scores.get(membre.id, 0) + 1
        
        # On met à jour le dernier gagnant
        old_winner = self.bot.get_user(self.last_winner_id)
        old_name = old_winner.display_name if old_winner else "Inconnu"
        self.last_winner_id = membre.id

        await interaction.response.send_message(
            f"🔄 **Correction !** Le point de la question n°{self.current_idx + 1} est retiré à **{old_name}** et attribué à **{membre.display_name}**.",
            ephemeral=False
        )

    @app_commands.command(name="next", description="[Staff] Question suivante.")
    @is_quiz_staff()
    async def next_question(self, interaction: discord.Interaction):
        if not self.answers:
            await interaction.response.send_message("❌ Charge d'abord un quiz.", ephemeral=True)
            return

        self.current_idx += 1
        if self.current_idx >= len(self.answers):
            await self._finish_quiz(interaction)
            return

        self.quiz_channel_id = interaction.channel_id
        self.is_listening = True
        self.last_winner_id = None
        await self.set_channel_lock(interaction.channel, False)
        
        await interaction.response.send_message(
            f"🏁 **Question n°{self.current_idx + 1} !**\nLe salon est ouvert !",
            ephemeral=False
        )

    async def _finish_quiz(self, interaction: discord.Interaction):
        if not self.scores:
            await interaction.response.send_message("🏁 Quiz terminé !")
        else:
            sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
            top_3 = sorted_scores[:3]
            embed = discord.Embed(title="🏆 Résultats du Quiz", color=discord.Color.gold())
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for i, (uid, pts) in enumerate(top_3):
                user = self.bot.get_user(uid)
                name = user.display_name if user else f"Joueur {uid}"
                lines.append(f"{medals[i]} **{name}** : {pts} point(s)")
            embed.description = "\n".join(lines)
            await interaction.response.send_message(embed=embed)

        await self.set_channel_lock(interaction.channel, True)
        self.answers = []
        self.current_idx = -1
        self.is_listening = False

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "❌ Cette commande est réservée au staff et aux animateurs.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue : {error}",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not self.is_listening:
            return
        if message.channel.id != self.quiz_channel_id:
            return

        # On utilise désormais / comme séparateur
        expected_raw = self.answers[self.current_idx]
        valid_variants = [normalize_text(v) for v in expected_raw.split('/')]
        
        if normalize_text(message.content) in valid_variants:
            self.is_listening = False
            uid = message.author.id
            self.scores[uid] = self.scores.get(uid, 0) + 1
            self.last_winner_id = uid
            
            await message.channel.send(
                f"🎉 **{message.author.display_name}** a trouvé ! La réponse était : **{expected_raw}**.\n"
                f"*Salon verrouillé.*"
            )
            await self.set_channel_lock(message.channel, True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))
