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

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

async def lese_google_sheet():
    """Liest das Google Sheet (CSV) aus und gibt es als Liste zurück."""
    async with aiohttp.ClientSession() as session:
        async with session.get(GOOGLE_SHEET_CSV_URL) as resp:
            text = await resp.text()
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]

@bot.command()
async def depot(ctx):
    """Zeigt das aktuelle Depot an."""
    daten = await lese_google_sheet()
    gesamt = sum(float(d["Wert"]) for d in daten)
    msg = f"📊 **Depotübersicht**\n💰 Gesamtwert: {gesamt:,.2f} €\n\n"
    for d in daten:
        aktie = d["Aktie"]
        wert = float(d["Wert"])
        veraenderung = float(d["Veränderung"])
        emoji = "📈" if veraenderung > 0 else ("📉" if veraenderung < 0 else "➖")
        msg += f"{emoji} {aktie}: {wert:,.2f} € ({veraenderung:+.2f}%)\n"
    await ctx.send(msg)

@tasks.loop(hours=24)
async def tages_update():
    """Postet jeden Tag ein Update automatisch."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    daten = await lese_google_sheet()
    gesamt = sum(float(d["Wert"]) for d in daten)
    await channel.send(f"📆 **Tagesupdate:** Gesamtwert: {gesamt:,.2f} €")

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    tages_update.start()

bot.run(DISCORD_TOKEN)
