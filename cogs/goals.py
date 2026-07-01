"""
cogs/goals.py
Member-facing commands: /goal-start, /checkin, /my-goals, /active-goals,
/goal-pause, /goal-resume, /goal-abandon.
"""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import embeds
import config


class GoalStartModal(discord.ui.Modal, title="Start a new goal"):
    goal_title = discord.ui.TextInput(
        label="Goal title",
        placeholder="e.g. Build a Discord bot in Python",
        max_length=100,
        required=True,
    )
    success_description = discord.ui.TextInput(
        label="What does success look like?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe your goal in detail — what are you building or working "
        "toward, and how will you know it's done?",
        max_length=500,
        required=True,
    )
    timeline = discord.ui.TextInput(
        label="Timeline (optional)",
        placeholder="e.g. 6 weeks, by end of August, or leave blank",
        max_length=50,
        required=False,
    )

    def __init__(self, cog: "Goals"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        username = interaction.user.name

        member = interaction.guild.get_member(interaction.user.id) or interaction.user

        db.ensure_user(discord_id, username)
        goal_num = db.next_goal_number(discord_id)
        goal_id = f"g-{username.lower()}-{goal_num}"

        db.create_goal(
            goal_id=goal_id,
            discord_id=discord_id,
            title=self.goal_title.value,
            description=self.success_description.value,
            timeline=self.timeline.value or None,
        )

        embed = embeds.goal_started_embed(
            member,
            goal_id,
            self.goal_title.value,
            self.success_description.value,
            self.timeline.value,
        )

        channel = discord.utils.get(
            interaction.guild.text_channels, name=config.GOAL_CHANNEL_NAME
        )
        if channel:
            await channel.send(embed=embed)

        await interaction.response.send_message(
            f"✨ Goal **{goal_id}** created! Posted in #{config.GOAL_CHANNEL_NAME}.",
            ephemeral=True,
        )


class Goals(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- /goal-start ----------

    @app_commands.command(name="goal-start", description="Share a new goal you're starting")
    async def goal_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GoalStartModal(self))

    # ---------- /checkin ----------

    @app_commands.command(name="checkin", description="Post a progress update on one of your goals")
    @app_commands.describe(
        goal="Which goal is this update for",
        update="What's the progress?",
        screenshot="Optional screenshot of your progress",
    )
    async def checkin(
        self,
        interaction: discord.Interaction,
        goal: str,
        update: str,
        screenshot: discord.Attachment = None,
    ):
        goal_row = db.get_goal(goal)
        if not goal_row or goal_row["discord_id"] != str(interaction.user.id):
            await interaction.response.send_message(
                "I couldn't find that goal under your name. Try `/my-goals` to see your active goal IDs.",
                ephemeral=True,
            )
            return
        if goal_row["status"] != "active":
            await interaction.response.send_message(
                f"That goal is currently **{goal_row['status']}**, so it's not accepting check-ins "
                f"right now. Use `/goal-resume` first if you paused it.",
                ephemeral=True,
            )
            return

        attachment_url = screenshot.url if screenshot else None
        db.add_checkin(goal, str(interaction.user.id), update, attachment_url)

        embed = embeds.checkin_embed(
            interaction.user, goal, goal_row["title"], update, attachment_url
        )

        channel = discord.utils.get(
            interaction.guild.text_channels, name=config.GOAL_CHANNEL_NAME
        )
        if channel:
            await channel.send(embed=embed)

        await interaction.response.send_message("✨ Check-in posted!", ephemeral=True)

    @checkin.autocomplete("goal")
    async def checkin_autocomplete(self, interaction: discord.Interaction, current: str):
        goals = db.get_user_goals(str(interaction.user.id), status="active")
        return [
            app_commands.Choice(name=f"{g['title']} ({g['goal_id']})", value=g["goal_id"])
            for g in goals
            if current.lower() in g["title"].lower()
        ][:25]

    # ---------- /my-goals ----------

    @app_commands.command(name="my-goals", description="See your own goals and their status")
    async def my_goals(self, interaction: discord.Interaction):
        goals = db.get_user_goals(str(interaction.user.id))
        if not goals:
            await interaction.response.send_message(
                "You don't have any goals yet — try `/goal-start` ✨", ephemeral=True
            )
            return

        lines = []
        for g in goals:
            last = g["last_checkin_at"] or "no check-ins yet"
            lines.append(f"**{g['goal_id']}** — {g['title']} · `{g['status']}` · last: {last}")

        embed = discord.Embed(
            title="✨ Your goals",
            description="\n".join(lines),
            color=config.COLOR_CHECKIN,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------- /active-goals ----------

    @app_commands.command(name="active-goals", description="See everyone's active goals")
    async def active_goals(self, interaction: discord.Interaction):
        goals = db.get_all_active_goals()
        if not goals:
            embed = discord.Embed(
                description="No active goals right now ✨", color=config.COLOR_CHECKIN
            )
            await interaction.response.send_message(embed=embed)
            return

        lines = []
        for g in goals:
            member = interaction.guild.get_member(int(g["discord_id"]))
            name = member.display_name if member else g["discord_id"]
            last = g["last_checkin_at"] or "no check-ins yet"
            lines.append(f"**{g['goal_id']}** — {g['title']} · {name} · last: {last}")

        embed = discord.Embed(
            title="✨ Active goals",
            description="\n".join(lines),
            color=config.COLOR_CHECKIN,
        )
        await interaction.response.send_message(embed=embed)

    # ---------- /maxxy-help ----------

    @app_commands.command(name="maxxy-help", description="See everything Maxxy can do")
    async def maxxy_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✨ What Maxxy can do",
            description="Your accountability buddy — here's the full command list.",
            color=config.COLOR_CHECKIN,
        )
        embed.add_field(
            name="🌱 Starting & managing a goal",
            value=(
                "`/goal-start` — share a new goal (title, what success looks like, timeline)\n"
                "`/goal-pause` — pause a goal, no reminders while paused\n"
                "`/goal-resume` — resume a paused goal\n"
                "`/goal-abandon` — drop a goal you're no longer pursuing, no judgment"
            ),
            inline=False,
        )
        embed.add_field(
            name="💫 Tracking progress",
            value=(
                "`/checkin` — post a progress update (text + optional screenshot) on one of your goals\n"
                "`/my-goals` — see your own goals and their status\n"
                "`/active-goals` — see everyone's active goals across the server"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ Senior / admin / TAMBAY only",
            value=(
                "`/goal-verify` — mark a check-in as seen and counted\n"
                "`/goal-achieved` — mark a goal as fully completed 🎉"
            ),
            inline=False,
        )
        embed.set_footer(
            text="Reminders happen on day 3 (public), day 6 (DM), and day 9 (admin alert) "
                 "since your last check-in. ✨"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------- /goal-pause, /goal-resume, /goal-abandon ----------

    async def _change_status(self, interaction, goal_id, new_status, event_type, verb):
        goal_row = db.get_goal(goal_id)
        if not goal_row or goal_row["discord_id"] != str(interaction.user.id):
            await interaction.response.send_message(
                "I couldn't find that goal under your name.", ephemeral=True
            )
            return
        db.set_status(goal_id, str(interaction.user.id), new_status, event_type)
        await interaction.response.send_message(
            f"✨ **{goal_id}** has been {verb}.", ephemeral=True
        )

    @app_commands.command(name="goal-pause", description="Pause one of your goals")
    @app_commands.describe(goal="Which goal to pause")
    async def goal_pause(self, interaction: discord.Interaction, goal: str):
        await self._change_status(interaction, goal, "paused", "paused", "paused — no reminders while paused")

    @goal_pause.autocomplete("goal")
    async def goal_pause_autocomplete(self, interaction: discord.Interaction, current: str):
        goals = db.get_user_goals(str(interaction.user.id), status="active")
        return [
            app_commands.Choice(name=f"{g['title']} ({g['goal_id']})", value=g["goal_id"])
            for g in goals
            if current.lower() in g["title"].lower()
        ][:25]

    @app_commands.command(name="goal-resume", description="Resume one of your paused goals")
    @app_commands.describe(goal="Which goal to resume")
    async def goal_resume(self, interaction: discord.Interaction, goal: str):
        await self._change_status(interaction, goal, "active", "resumed", "resumed — welcome back ✨")

    @goal_resume.autocomplete("goal")
    async def goal_resume_autocomplete(self, interaction: discord.Interaction, current: str):
        goals = db.get_user_goals(str(interaction.user.id), status="paused")
        return [
            app_commands.Choice(name=f"{g['title']} ({g['goal_id']})", value=g["goal_id"])
            for g in goals
            if current.lower() in g["title"].lower()
        ][:25]

    @app_commands.command(name="goal-abandon", description="Drop a goal you no longer want to pursue")
    @app_commands.describe(goal="Which goal to abandon")
    async def goal_abandon(self, interaction: discord.Interaction, goal: str):
        await self._change_status(interaction, goal, "abandoned", "abandoned", "abandoned — no judgment, you can always start a new one")

    @goal_abandon.autocomplete("goal")
    async def goal_abandon_autocomplete(self, interaction: discord.Interaction, current: str):
        goals = db.get_user_goals(str(interaction.user.id))
        return [
            app_commands.Choice(name=f"{g['title']} ({g['goal_id']})", value=g["goal_id"])
            for g in goals
            if g["status"] in ("active", "paused") and current.lower() in g["title"].lower()
        ][:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(Goals(bot))
