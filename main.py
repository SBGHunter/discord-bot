import os
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks, commands

# --- Konfiguration über Environment Variables ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
SITE_BASE = os.environ.get("SITE_BASE", "https://example.com")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot_http")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

session = None

async def fetch_data():
    """Ruft einfache Daten von einer Website ab."""
    global session
    if session is None:
        session = aiohttp.ClientSession()
    async with session.get(SITE_BASE) as resp:
        html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "Kein Titel gefunden"
    return f"Seitentitel: {title}"

@bot.event
async def on_ready():
    log.info(f"✅ Bot online als {bot.user}")
    periodic_task.start()

@tasks.loop(minutes=1)
async def periodic_task():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        log.error("Channel nicht gefunden.")
        return
    try:
        data = await fetch_data()
        await channel.send(f"📡 Website-Daten:\n```\n{data}\n```")
    except Exception as e:
        await channel.send(f"⚠️ Fehler: {e}")

@bot.command()
async def check(ctx):
    """Manueller Check: !check"""
    data = await fetch_data()
    await ctx.send(f"👀 Ergebnis:\n```\n{data}\n```")

bot.run(DISCORD_TOKEN)
