"""
bot.py
Entry point. Run this file to start Maxxy: python bot.py
"""

import asyncio
import discord
from discord.ext import commands

import config
import database as db

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",  # prefix unused; we're slash-command only
    intents=intents,
    application_id=config.APPLICATION_ID,
)


@bot.event
async def on_ready():
    print(f"✨ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    # Sync runs here, not before bot.start(), because the bot's internal
    # connection state isn't fully ready until on_ready fires.
    synced = await bot.tree.sync()
    print(f"✨ Synced {len(synced)} slash commands")


async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError(
            "MAXXY_BOT_TOKEN environment variable is not set. "
            "See the deployment instructions for how to set this."
        )
    if not config.APPLICATION_ID:
        raise RuntimeError(
            "MAXXY_APPLICATION_ID environment variable is not set. "
            "Find this in the Discord Developer Portal under General Information -> Application ID."
        )

    db.init_db()

    async with bot:
        await bot.load_extension("cogs.goals")
        await bot.load_extension("cogs.admin")
        await bot.load_extension("cogs.scheduler")
        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())