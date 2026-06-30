"""
cogs/scheduler.py
The daily sweep. Runs once every 24 hours, checks every active goal's days-since-checkin,
and fires the appropriate escalation step (public tag -> DM -> admin alert) exactly once
per threshold, using last_reminder_threshold to avoid repeat firing.
"""

import datetime
import discord
from discord.ext import commands, tasks

import database as db
import embeds
import config


def days_since(iso_timestamp: str) -> int:
    then = datetime.datetime.fromisoformat(iso_timestamp)
    now = datetime.datetime.utcnow()
    return (now - then).days


class Scheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_sweep.start()

    def cog_unload(self):
        self.daily_sweep.cancel()

    @tasks.loop(hours=24)
    async def daily_sweep(self):
        goals = db.get_all_active_goals()

        for guild in self.bot.guilds:
            goal_channel = discord.utils.get(
                guild.text_channels, name=config.GOAL_CHANNEL_NAME
            )
            alert_channel = discord.utils.get(
                guild.text_channels, name=config.ADMIN_ALERT_CHANNEL_NAME
            )

            for g in goals:
                member = guild.get_member(int(g["discord_id"]))
                if not member:
                    continue  # goal owner isn't in this guild, skip

                # baseline: time since last checkin, or since goal creation if never checked in
                reference_ts = g["last_checkin_at"] or g["created_at"]
                elapsed = days_since(reference_ts)
                threshold_already_sent = g["last_reminder_threshold"]

                if elapsed >= config.REMINDER_DAY_ADMIN_ALERT and threshold_already_sent < config.REMINDER_DAY_ADMIN_ALERT:
                    if alert_channel:
                        last_str = g["last_checkin_at"] or "never"
                        embed = embeds.admin_alert_embed(member, g["title"], g["goal_id"], last_str)
                        await alert_channel.send(embed=embed)
                    db.log_reminder(g["goal_id"], g["discord_id"], config.REMINDER_DAY_ADMIN_ALERT)

                elif elapsed >= config.REMINDER_DAY_DM and threshold_already_sent < config.REMINDER_DAY_DM:
                    try:
                        embed = embeds.reminder_dm_embed(g["title"])
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        pass  # DMs closed; the day-9 admin alert will still catch this
                    db.log_reminder(g["goal_id"], g["discord_id"], config.REMINDER_DAY_DM)

                elif elapsed >= config.REMINDER_DAY_PUBLIC and threshold_already_sent < config.REMINDER_DAY_PUBLIC:
                    if goal_channel:
                        embed = embeds.reminder_public_embed(member, g["title"], g["goal_id"])
                        await goal_channel.send(embed=embed)
                    db.log_reminder(g["goal_id"], g["discord_id"], config.REMINDER_DAY_PUBLIC)

    @daily_sweep.before_loop
    async def before_sweep(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Scheduler(bot))
