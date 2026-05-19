"""
Composants d'interface : boutons, menus déroulants, modales.

Flux de création d'annonce :
  PanelView (boutons permanents)
    → TCGSelectView (menu TCG)
      → ListingModal (formulaire)
        → ConditionSelectView (menu état)  [sauf type achat]
          → PhotoView (lien photo / passer)
            → RecapView (publier / annuler)
              → post forum créé

ListingActionsView : boutons sur le post publié.
"""
import discord

import config
from cogs import embeds, routing
from database.models import db


# ════════════════════════════════════════════════════════════
# 1. PANNEAU PERMANENT
# ════════════════════════════════════════════════════════════
class PanelView(discord.ui.View):
    """Panneau permanent avec les boutons de création d'annonce."""

    def __init__(self):
        super().__init__(timeout=None)  # persistant

    @discord.ui.button(label="Vendre", style=discord.ButtonStyle.success,
                       emoji="🛒", custom_id="mkt:new:vente")
    async def vente(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._start(interaction, "vente")

    @discord.ui.button(label="Acheter", style=discord.ButtonStyle.primary,
                       emoji="💰", custom_id="mkt:new:achat")
    async def achat(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._start(interaction, "achat")

    @discord.ui.button(label="Scellé", style=discord.ButtonStyle.secondary,
                       emoji="📦", custom_id="mkt:new:scelle")
    async def scelle(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._start(interaction, "scelle")

    @staticmethod
    async def _start(interaction: discord.Interaction, listing_type: str):
        await interaction.response.send_message(
            "Sélectionne le TCG :",
            view=TCGSelectView(listing_type),
            ephemeral=True,
        )


# ════════════════════════════════════════════════════════════
# 2. MENU TCG
# ════════════════════════════════════════════════════════════
class TCGSelectView(discord.ui.View):
    def __init__(self, listing_type: str):
        super().__init__(timeout=300)
        self.listing_type = listing_type

        options = [
            discord.SelectOption(label=data["name"], value=key, emoji=data["emoji"])
            for key, data in config.TCG_CHOICES.items()
        ]
        select = discord.ui.Select(placeholder="Choisis un TCG...", options=options)
        select.callback = self._on_select
        self._select = select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        tcg_key = self._select.values[0]
        await interaction.response.send_modal(
            ListingModal(self.listing_type, tcg_key)
        )


# ════════════════════════════════════════════════════════════
# 3. FORMULAIRE (MODAL)
# ════════════════════════════════════════════════════════════
class ListingModal(discord.ui.Modal):
    """Formulaire de saisie des infos de l'annonce."""

    def __init__(self, listing_type: str, tcg_key: str):
        ltype = config.LISTING_TYPES[listing_type]
        tcg = config.TCG_CHOICES[tcg_key]
        super().__init__(title=f"{ltype['label']} — {tcg['name']}"[:45], timeout=900)

        self.listing_type = listing_type
        self.tcg_key = tcg_key

        self.card_name = discord.ui.TextInput(
            label="Nom de la carte / produit",
            placeholder="Ex : Charizard ex",
            max_length=100,
            required=True,
        )
        self.add_item(self.card_name)

        self.card_set = discord.ui.TextInput(
            label="Set / Extension",
            placeholder="Ex : Obsidian Flames",
            max_length=100,
            required=False,
        )
        self.add_item(self.card_set)

        # Prix uniquement si le type le demande (vente, scellé)
        self.price = None
        if ltype["has_price"]:
            self.price = discord.ui.TextInput(
                label="Prix (EUR)",
                placeholder="Ex : 85",
                max_length=10,
                required=True,
            )
            self.add_item(self.price)

        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="État, détails, conditions d'envoi...",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False,
        )
        self.add_item(self.description)

        self.location = discord.ui.TextInput(
            label="Localisation (ville)",
            placeholder="Ex : Lyon",
            max_length=50,
            required=False,
        )
        self.add_item(self.location)

    async def on_submit(self, interaction: discord.Interaction):
        # Validation prix
        price_value = None
        if self.price is not None:
            raw = self.price.value.replace(",", ".").replace("€", "").strip()
            try:
                price_value = round(float(raw), 2)
                if price_value < 0:
                    raise ValueError
            except ValueError:
                await interaction.response.send_message(
                    "❌ Prix invalide. Entre un nombre (ex : 85 ou 85.50).",
                    ephemeral=True,
                )
                return

        draft = {
            "listing_type": self.listing_type,
            "tcg": self.tcg_key,
            "card_name": self.card_name.value.strip(),
            "card_set": self.card_set.value.strip() or None,
            "price": price_value,
            "description": self.description.value.strip() or None,
            "location": self.location.value.strip() or None,
            "condition": None,
            "photo_url": None,
        }

        # Achat → pas d'état de carte demandé, on saute à la photo
        if self.listing_type == "achat":
            await interaction.response.send_message(
                "📸 Ajoute une photo (ou passe) :",
                view=PhotoView(draft),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Sélectionne l'état :",
                view=ConditionSelectView(draft),
                ephemeral=True,
            )


# ════════════════════════════════════════════════════════════
# 4. MENU ÉTAT
# ════════════════════════════════════════════════════════════
class ConditionSelectView(discord.ui.View):
    def __init__(self, draft: dict):
        super().__init__(timeout=300)
        self.draft = draft

        options = [
            discord.SelectOption(label=data["name"], value=key, emoji=data["emoji"])
            for key, data in config.CARD_CONDITIONS.items()
        ]
        select = discord.ui.Select(placeholder="État de la carte...", options=options)
        select.callback = self._on_select
        self._select = select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        self.draft["condition"] = self._select.values[0]
        await interaction.response.send_message(
            "📸 Ajoute une photo (ou passe) :",
            view=PhotoView(self.draft),
            ephemeral=True,
        )


# ════════════════════════════════════════════════════════════
# 5. PHOTO
# ════════════════════════════════════════════════════════════
class PhotoView(discord.ui.View):
    def __init__(self, draft: dict):
        super().__init__(timeout=300)
        self.draft = draft

    @discord.ui.button(label="Ajouter un lien photo", style=discord.ButtonStyle.primary, emoji="🔗")
    async def add_link(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(PhotoLinkModal(self.draft))

    @discord.ui.button(label="Passer", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def skip(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_message(
            embed=embeds.build_recap_embed(self.draft),
            view=RecapView(self.draft),
            ephemeral=True,
        )


class PhotoLinkModal(discord.ui.Modal, title="Lien de l'image"):
    def __init__(self, draft: dict):
        super().__init__(timeout=300)
        self.draft = draft
        self.url = discord.ui.TextInput(
            label="URL de l'image",
            placeholder="https://i.imgur.com/...",
            max_length=500,
            required=True,
        )
        self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        url = self.url.value.strip()
        if not url.startswith(("http://", "https://")):
            await interaction.response.send_message(
                "❌ URL invalide (doit commencer par http:// ou https://).",
                ephemeral=True,
            )
            return
        self.draft["photo_url"] = url
        await interaction.response.send_message(
            embed=embeds.build_recap_embed(self.draft),
            view=RecapView(self.draft),
            ephemeral=True,
        )


# ════════════════════════════════════════════════════════════
# 6. RÉCAP + PUBLICATION
# ════════════════════════════════════════════════════════════
class RecapView(discord.ui.View):
    def __init__(self, draft: dict):
        super().__init__(timeout=300)
        self.draft = draft

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_message(
            "Annonce annulée. Relance depuis le panneau pour recommencer.",
            ephemeral=True,
        )

    @discord.ui.button(label="Publier", style=discord.ButtonStyle.success, emoji="✅")
    async def publish(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._publish(interaction)

    async def _publish(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        # Trouver le forum cible
        forum = routing.find_forum_for_tcg(guild, self.draft["tcg"])
        if forum is None:
            tcg = config.TCG_CHOICES[self.draft["tcg"]]
            await interaction.response.send_message(
                f"❌ Forum `{tcg['forum']}` introuvable. Préviens un admin.",
                ephemeral=True,
            )
            return

        # Enregistrer en base
        user_id = db.get_or_create_user(str(author.id), author.name)
        listing_data = dict(self.draft, user_id=user_id)
        listing_id = db.create_listing(listing_data)

        # Construire le post
        title = embeds.build_listing_title(self.draft)
        embed = embeds.build_listing_embed(self.draft, author)
        tags = routing.resolve_tags(forum, self.draft)

        try:
            created = await forum.create_thread(
                name=title,
                embed=embed,
                applied_tags=tags,
                view=ListingActionsView(listing_id),
            )
            db.set_listing_post_id(listing_id, str(created.thread.id))
            await interaction.response.send_message(
                f"✅ Annonce publiée ! → {created.thread.jump_url}",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Le bot n'a pas la permission de poster dans ce forum.",
                ephemeral=True,
            )
        except Exception as e:  # noqa: BLE001
            await interaction.response.send_message(
                f"❌ Erreur lors de la publication : `{e}`",
                ephemeral=True,
            )


# ════════════════════════════════════════════════════════════
# 7. ACTIONS SUR LE POST PUBLIÉ
# ════════════════════════════════════════════════════════════
class ListingActionsView(discord.ui.View):
    """Boutons attachés au post d'annonce.

    `listing_id` n'est pas connu au redémarrage du bot pour les vieux
    posts ; les actions retrouvent l'annonce via l'ID du thread.
    """

    def __init__(self, listing_id: int = 0):
        super().__init__(timeout=None)
        self.listing_id = listing_id

    @discord.ui.button(label="Contacter", style=discord.ButtonStyle.primary,
                       emoji="💬", custom_id="mkt:post:contact")
    async def contact(self, interaction: discord.Interaction, _button: discord.ui.Button):
        thread = interaction.channel
        owner_id = getattr(thread, "owner_id", None)
        owner = interaction.guild.get_member(owner_id) if owner_id else None
        if owner:
            await interaction.response.send_message(
                f"💬 Pour négocier, écris en MP à {owner.mention}.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "💬 Contacte l'auteur de l'annonce en message privé.",
                ephemeral=True,
            )

    @discord.ui.button(label="Marquer comme vendu", style=discord.ButtonStyle.secondary,
                       emoji="🔴", custom_id="mkt:post:sold")
    async def mark_sold(self, interaction: discord.Interaction, _button: discord.ui.Button):
        thread = interaction.channel
        owner_id = getattr(thread, "owner_id", None)

        # Seul l'auteur (ou un admin) peut clôturer
        is_admin = interaction.user.guild_permissions.manage_messages
        if interaction.user.id != owner_id and not is_admin:
            await interaction.response.send_message(
                "❌ Seul l'auteur de l'annonce peut la clôturer.",
                ephemeral=True,
            )
            return

        # Mettre à jour le tag de statut + le titre
        try:
            forum = thread.parent
            sold_tag = next(
                (t for t in forum.available_tags if t.name == config.SOLD_STATUS_TAG),
                None,
            )
            new_tags = [
                t for t in thread.applied_tags
                if t.name not in (config.DEFAULT_STATUS_TAG, "En négo")
            ]
            if sold_tag:
                new_tags.append(sold_tag)

            new_name = thread.name
            if not new_name.startswith("✅"):
                new_name = f"✅ {new_name}"[:100]

            await thread.edit(
                name=new_name,
                applied_tags=new_tags[:5],
                archived=True,
                locked=True,
            )

            listing = db.get_listing_by_post(str(thread.id))
            if listing:
                db.set_listing_status(listing["id"], "vendu")

            await interaction.response.send_message(
                "✅ Annonce marquée comme vendue et archivée.",
                ephemeral=True,
            )
        except Exception as e:  # noqa: BLE001
            await interaction.response.send_message(
                f"❌ Erreur : `{e}`",
                ephemeral=True,
            )
