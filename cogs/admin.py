"""
cogs/admin.py
Senior / admin / TAMBAY-only commands: /goal-verify, /goal-achieved.
"""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import embeds
import config


def has_verifier_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        member_roles = {r.name for r in interaction.user.roles}
        if not member_roles.intersection(config.VERIFIER_ROLES):
            await interaction.response.send_message(
                "This command is only available to Senior, admin, or TAMBAY roles.",
                ephemeral=True,
            )
            return False
        return True
    return app_commands.check(predicate)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="goal-verify", description="Verify someone's check-in as real progress")
    @app_commands.describe(goal="Which goal to verify")
    @has_verifier_role()
    async def goal_verify(self, interaction: discord.Interaction, goal: str):
        goal_row = db.get_goal(goal)
        if not goal_row:
            await interaction.response.send_message("No goal found with that ID.", ephemeral=True)
            return

        db.mark_verified(goal, str(interaction.user.id))

        member = interaction.guild.get_member(int(goal_row["discord_id"]))
        embed = embeds.verified_embed(member, interaction.user)
        await interaction.response.send_message(embed=embed)

    @goal_verify.autocomplete("goal")
    async def goal_verify_autocomplete(self, interaction: discord.Interaction, current: str):
        goals = db.get_all_active_goals()
        return [
            app_commands.Choice(name=f"{g['title']} ({g['goal_id']})", value=g["goal_id"])
            for g in goals
            if current.lower() in g["title"].lower()
        ][:25]

    @app_commands.command(name="goal-achieved", description="Mark a goal as fully achieved")
    @app_commands.describe(goal="Which goal was achieved")
    @has_verifier_role()
    async def goal_achieved(self, interaction: discord.Interaction, goal: str):
        goal_row = db.get_goal(goal)
        if not goal_row:
            await interaction.response.send_message("No goal found with that ID.", ephemeral=True)
            return

        db.mark_achieved(goal, str(interaction.user.id))

        member = interaction.guild.get_member(int(goal_row["discord_id"]))
        embed = embeds.goal_achieved_embed(
            member, interaction.user, goal_row["title"], goal_row["description"]
        )
        await interaction.response.send_message(embed=embed)

    @goal_achieved.autocomplete("goal")
    async def goal_achieved_autocomplete(self, interaction: discord.Interaction, current: str):
        goals = db.get_all_active_goals()
        return [
            app_commands.Choice(name=f"{g['title']} ({g['goal_id']})", value=g["goal_id"])
            for g in goals
            if current.lower() in g["title"].lower()
        ][:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
