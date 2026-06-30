"""
config.py
All the "tune this without digging through cogs" values live here:
embed colors, channel names/IDs, and the role names allowed to verify/achieve goals.
"""

import os

# ---------- Discord channel names (set these to match your server exactly) ----------
GOAL_CHANNEL_NAME = "goal-tracker"       # combined: started, checkins, achieved
ADMIN_ALERT_CHANNEL_NAME = "admin-and-sr"

# ---------- Roles allowed to /goal-verify and /goal-achieved ----------
VERIFIER_ROLES = ["Senior", "admin", "TAMBAY"]

# ---------- Embed colors (Maxxy palette: dark plum / cyan / magenta) ----------
COLOR_STARTED = 0x00E5FF      # cyan — new goal
COLOR_CHECKIN = 0xFF4FD8      # magenta — routine update
COLOR_VERIFIED = 0x00B8A9     # deep teal — seen & confirmed
COLOR_ACHIEVED = 0xFFC857     # gold — celebration, breaks from the cool palette on purpose
COLOR_REMINDER = 0xC74FAE     # muted magenta — gentle nudge, not alarming
COLOR_ALERT = 0x8A8A99        # neutral grey — informational, admin-only

# ---------- Escalation thresholds (calendar days since last check-in) ----------
REMINDER_DAY_PUBLIC = 3
REMINDER_DAY_DM = 6
REMINDER_DAY_ADMIN_ALERT = 9

# ---------- Bot token (read from environment, never hardcoded) ----------
BOT_TOKEN = os.environ.get("MAXXY_BOT_TOKEN")
APPLICATION_ID = os.environ.get("MAXXY_APPLICATION_ID")
