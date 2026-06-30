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

bot = commands.Bot(command_prefix="!", intents=intents)  # prefix unused; we're slash-command only


@bot.event
async def on_ready():
    print(f"✨ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


async def main():
    db.init_db()

    async with bot:
        await bot.load_extension("cogs.goals")
        await bot.load_extension("cogs.admin")
        await bot.load_extension("cogs.scheduler")

        # Sync slash commands with Discord. This registers them globally,
        # which can take up to an hour to propagate on first sync.
        # For instant updates during development, sync to a single test guild instead —
        # see the deployment instructions for how to do that.
        await bot.tree.sync()

        if not config.BOT_TOKEN:
            raise RuntimeError(
                "MAXXY_BOT_TOKEN environment variable is not set. "
                "See the deployment instructions for how to set this."
            )

        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
