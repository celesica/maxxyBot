"""
embeds.py
One place to build every embed Maxxy sends, so the message templates we designed
stay consistent no matter which cog triggers them.
"""

import discord
import config


def goal_started_embed(member: discord.Member, goal_id, title, description, timeline):
    embed = discord.Embed(
        title="📌 New Goal Alert!",
        description=f"{member.mention} just started something new.",
        color=config.COLOR_STARTED,
    )
    embed.add_field(name="Goal", value=title, inline=False)
    embed.add_field(name="What success looks like", value=description, inline=False)
    if timeline:
        embed.add_field(name="Timeline", value=timeline, inline=False)
    embed.set_footer(text=f"Goal ID: {goal_id} · Let's cheer them on! ✨")
    return embed


def checkin_embed(member: discord.Member, goal_id, title, update_text, attachment_url=None):
    embed = discord.Embed(
        title="✨ Progress Update",
        description=f"{member.mention} checked in on **{title}**",
        color=config.COLOR_CHECKIN,
    )
    embed.add_field(name="Update", value=update_text, inline=False)
    if attachment_url:
        embed.set_image(url=attachment_url)
    embed.set_footer(text=f"Goal ID: {goal_id} · awaiting verification")
    return embed


def verified_embed(member: discord.Member, admin: discord.Member):
    embed = discord.Embed(
        description=f"✨ Seen and Verified by {admin.mention}.\n"
        f"Keep going, {member.mention} — this is how it gets done. 💫",
        color=config.COLOR_VERIFIED,
    )
    return embed


def goal_achieved_embed(member: discord.Member, admin: discord.Member, title, description):
    embed = discord.Embed(
        title="🎉✨ GOAL ACHIEVED ✨🎉",
        description=f"{member.mention} just completed: **{title}**",
        color=config.COLOR_ACHIEVED,
    )
    embed.add_field(name="What they set out to do", value=description, inline=False)
    embed.set_footer(text=f"Confirmed by {admin.display_name} · From day one to done 🌟")
    return embed


def reminder_public_embed(member: discord.Member, title, goal_id):
    embed = discord.Embed(
        description=f"✨ Hey {member.mention} — just checking in on **{title}**.\n"
        f"No update in a few days. How's it going?\n\n"
        f"Whenever you're ready, drop a `/checkin` 💫",
        color=config.COLOR_REMINDER,
    )
    embed.set_footer(text=f"Goal ID: {goal_id}")
    return embed


def reminder_dm_embed(title):
    embed = discord.Embed(
        description=f"✨ Hey, it's Maxxy.\n\n"
        f"It's been about a week since your last update on **{title}**. "
        f"No pressure — just wanted to check in privately rather than tag you publicly again.\n\n"
        f"If things shifted, you can always `/goal-pause` — no shame in that. "
        f"If you're just heads-down, a quick `/checkin` whenever works. I'm here either way. 💫",
        color=config.COLOR_REMINDER,
    )
    return embed


def admin_alert_embed(member: discord.Member, title, goal_id, last_checkin_str):
    embed = discord.Embed(
        title="⚠️ Stale Goal Flag",
        description=f"**{goal_id}** — *{title}*",
        color=config.COLOR_ALERT,
    )
    embed.add_field(name="Owner", value=member.mention, inline=True)
    embed.add_field(name="Last activity", value=last_checkin_str, inline=True)
    embed.set_footer(text="Might be worth a real check-in from a human. Maxxy won't auto-nudge further. ✨")
    return embed
