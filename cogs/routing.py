"""
Routage des annonces vers les bons forums + gestion des tags.

Isolé ici pour que la logique "où poster / quels tags" soit
modifiable sans toucher au reste.
"""
import discord

import config


def find_forum_for_tcg(guild: discord.Guild, tcg_key: str) -> discord.ForumChannel | None:
    """Trouve le ForumChannel correspondant à un TCG.

    Se base sur le champ 'forum' de config.TCG_CHOICES.
    """
    tcg = config.TCG_CHOICES.get(tcg_key)
    if not tcg:
        return None

    forum_name = tcg["forum"]
    for channel in guild.channels:
        if isinstance(channel, discord.ForumChannel) and channel.name == forum_name:
            return channel
    return None


def _find_tag(forum: discord.ForumChannel, tag_name: str) -> discord.ForumTag | None:
    """Cherche un tag par nom dans un forum (insensible à la casse)."""
    for tag in forum.available_tags:
        if tag.name.lower() == tag_name.lower():
            return tag
    return None


def resolve_tags(forum: discord.ForumChannel, listing: dict) -> list[discord.ForumTag]:
    """Détermine les tags à appliquer à un post selon l'annonce.

    Applique : type d'annonce + prix + état + statut "Disponible".
    Discord limite à 5 tags par post → on tronque.
    """
    tags: list[discord.ForumTag] = []

    # 1. Type d'annonce (Vente / Achat / Scellé)
    ltype = config.LISTING_TYPES.get(listing["listing_type"])
    if ltype:
        tag = _find_tag(forum, ltype["tag"])
        if tag:
            tags.append(tag)

    # 2. Fourchette de prix
    price = listing.get("price")
    if price is not None:
        for price_range in config.PRICE_RANGES:
            if price_range["min"] <= price < price_range["max"]:
                tag = _find_tag(forum, price_range["tag"])
                if tag:
                    tags.append(tag)
                break

    # 3. État de la carte
    condition = listing.get("condition")
    if condition:
        cond = config.CARD_CONDITIONS.get(condition)
        if cond:
            tag = _find_tag(forum, cond["tag"])
            if tag:
                tags.append(tag)

    # 4. Statut "Disponible"
    status_tag = _find_tag(forum, config.DEFAULT_STATUS_TAG)
    if status_tag:
        tags.append(status_tag)

    return tags[:5]  # Discord : max 5 tags par post
