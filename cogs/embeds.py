"""
Construction des embeds et titres d'annonces.

Centralise tout le "rendu visuel" pour qu'il soit facile à modifier
sans toucher à la logique d'interaction (dans views.py).
"""
import discord

import config
from database.models import db


def build_listing_title(listing: dict) -> str:
    """Construit le titre du post forum.

    Ex: "[VENTE] [POKÉMON] Charizard ex — 85€"
    """
    ltype = config.LISTING_TYPES[listing["listing_type"]]
    tcg = config.TCG_CHOICES[listing["tcg"]]

    title = f"{ltype['prefix']} [{tcg['name'].upper()}] {listing['card_name']}"
    if listing.get("price"):
        title += f" — {listing['price']}€"

    # Discord limite les titres de thread à 100 caractères
    return title[:100]


def build_listing_embed(listing: dict, author: discord.abc.User) -> discord.Embed:
    """Construit l'embed affiché dans le post forum."""
    tcg = config.TCG_CHOICES[listing["tcg"]]
    ltype = config.LISTING_TYPES[listing["listing_type"]]

    embed = discord.Embed(
        title=f"{tcg['emoji']} {listing['card_name']}",
        color=config.COLORS["marketplace"],
    )

    embed.add_field(name="Type", value=f"{ltype['emoji']} {ltype['label']}", inline=True)
    embed.add_field(name="TCG", value=f"{tcg['emoji']} {tcg['name']}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    if listing.get("card_set"):
        embed.add_field(name="📦 Set", value=listing["card_set"], inline=True)
    if listing.get("price"):
        embed.add_field(name="💰 Prix", value=f"**{listing['price']}€**", inline=True)
    if listing.get("condition"):
        cond = config.CARD_CONDITIONS.get(listing["condition"])
        if cond:
            embed.add_field(name="État", value=f"{cond['emoji']} {cond['name']}", inline=True)
    if listing.get("location"):
        embed.add_field(name="📍 Localisation", value=listing["location"], inline=False)
    if listing.get("description"):
        embed.add_field(name="📝 Description", value=listing["description"], inline=False)
    if listing.get("photo_url"):
        embed.set_image(url=listing["photo_url"])

    # Profil utilisateur
    profile = db.get_user_profile(str(author.id))
    if profile:
        is_buying = listing["listing_type"] == "achat"
        role_label = "Acheteur" if is_buying else "Vendeur"
        
        if profile["total_feedback"] > 0:
            stars = "⭐" * max(1, min(5, round(profile["reputation_avg"])))
            rep = f"{stars} {profile['reputation_avg']:.1f}/5 ({profile['total_feedback']} avis)"
        else:
            rep = f"Nouveau {role_label.lower()} (pas encore d'avis)"
            
        verified = "✅ Vérifié" if profile["verified"] else "🔰 Non vérifié"
        embed.add_field(
            name=f"👤 {role_label}",
            value=f"{author.mention} · {verified}\n{rep}",
            inline=False,
        )

    embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_recap_embed(draft: dict) -> discord.Embed:
    """Embed de récapitulatif avant publication (vu seulement par l'auteur)."""
    tcg = config.TCG_CHOICES[draft["tcg"]]
    ltype = config.LISTING_TYPES[draft["listing_type"]]

    embed = discord.Embed(
        title="🔍 Récapitulatif",
        description="Vérifie ton annonce avant de publier.",
        color=config.COLORS["info"],
    )
    embed.add_field(name="Type", value=f"{ltype['emoji']} {ltype['label']}", inline=True)
    embed.add_field(name="TCG", value=f"{tcg['emoji']} {tcg['name']}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Carte / produit", value=draft["card_name"], inline=False)

    if draft.get("card_set"):
        embed.add_field(name="Set", value=draft["card_set"], inline=True)
    if draft.get("price"):
        embed.add_field(name="Prix", value=f"{draft['price']}€", inline=True)
    if draft.get("condition"):
        cond = config.CARD_CONDITIONS.get(draft["condition"])
        if cond:
            embed.add_field(name="État", value=f"{cond['emoji']} {cond['name']}", inline=True)
    if draft.get("location"):
        embed.add_field(name="📍 Localisation", value=draft["location"], inline=False)
    if draft.get("description"):
        embed.add_field(name="📝 Description", value=draft["description"], inline=False)

    embed.add_field(
        name="Photo",
        value="✅ Ajoutée" if draft.get("photo_url") else "➡️ Aucune",
        inline=True,
    )
    return embed


def build_panel_embed() -> discord.Embed:
    """Embed du panneau permanent de création d'annonce."""
    embed = discord.Embed(
        title="🛒 Créer une annonce",
        description=(
            "Clique sur un bouton pour publier ton annonce.\n"
            "Le bot te guide étape par étape — ton annonce est ensuite "
            "postée automatiquement dans le bon salon TCG.\n\n"
            "🛒 **Vendre** — vendre une carte\n"
            "💰 **Acheter** — rechercher une carte\n"
            "📦 **Scellé** — vendre du sealed (boosters, displays, ETB)"
        ),
        color=config.COLORS["marketplace"],
    )
    embed.set_footer(text="Marketplace TCG")
    return embed


def build_profile_embed(user: discord.User | discord.Member, profile: dict) -> discord.Embed:
    """Construit l'embed de profil public d'un utilisateur."""
    is_verified = profile.get("verified", False)
    status_str = "✅ Utilisateur Vérifié" if is_verified else "🔰 Utilisateur Non Vérifié"
    
    embed = discord.Embed(
        title=f"Profil Marketplace de {user.display_name}",
        color=config.COLORS["success"] if is_verified else config.COLORS["info"]
    )
    
    # Étoiles et Moyenne
    avg = profile.get("reputation_avg", 0)
    total_feedback = profile.get("total_feedback", 0)
    stars = "⭐" * max(1, min(5, round(avg))) if total_feedback > 0 else "Aucune note"
    
    embed.add_field(
        name="Réputation", 
        value=f"{stars}\n**{avg:.2f} / 5** ({total_feedback} avis)", 
        inline=True
    )
    
    embed.add_field(
        name="Transactions", 
        value=f"📦 **{profile.get('total_transactions', 0)}** terminées", 
        inline=True
    )
    
    embed.add_field(name="Statut", value=status_str, inline=False)
    
    embed.set_thumbnail(url=user.display_avatar.url)
    
    # Formatage de la date pour Discord (ex: <t:12345678:R> affiche "il y a 2 jours")
    # On gère le cas où member_since est une string venant de SQLite
    since = profile.get("member_since", "")
    if since:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            timestamp = int(dt.timestamp())
            footer_text = f"Membre marketplace depuis le {dt.strftime('%d/%m/%Y')}"
            embed.set_footer(text=footer_text)
        except Exception:
            embed.set_footer(text="Membre marketplace")
    else:
        embed.set_footer(text="Membre marketplace")
    
    return embed
