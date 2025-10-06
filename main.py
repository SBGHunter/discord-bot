import os
import io
import csv
import aiohttp
import discord
from discord.ext import commands, tasks

# --- Konfiguration ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
GOOGLE_SHEET_CSV_URL = os.environ.get("GOOGLE_SHEET_CSV_URL")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Hilfsfunktionen ---
def parse_float(s):
    """Konvertiert einen String mit Komma als Dezimaltrennzeichen zu float."""
    try:
        return float(s.re
