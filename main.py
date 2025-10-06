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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Hilfsfunktionen ---
def parse_float(s):
    """Parst einen String zu float, ersetzt Komma durch Punkt und setzt ungültige Werte auf 0."""
    try:
        return float(s.replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0

async def lese_google_sheet():
    """Liest das Google Sheet (CSV) aus und gibt es als Liste von Dicts zurück."""
    async with aiohttp.ClientSession() as session:
        async with session.get(GOOGLE_SHEET_CSV_URL) as resp:
            text = await resp.text()
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]

# --- Commands ---
@bot.command()
async def depot(ctx):
    """Zeigt das aktuelle Depot an."""
    daten = await lese_google_sheet()
    gesamt = sum(parse_float(d["Wert"]) for d in daten)
    msg = f"📊 **Depotübersicht**\n💰 Gesamtwert: {gesamt:,.2f} €\n\n"
    for d in daten:
        aktie = d.get("Aktie", "Unbekannt")
        wert = parse_float(d.get("Wert", "0"))
        veraenderung = parse_float(d.get("Veränderung", "0"))
        emoji = "📈" if veraenderung > 0 else ("📉" if veraenderung < 0 else "➖")
        msg += f"{emoji} {aktie}: {wert:,.2f} € ({veraenderung:+.2f}%)\n"
    await ctx.send(msg)

# --- Tasks ---
@tasks.loop(minutes=10)
async def tages_update():
    """Postet automatisch Updates in den Kanal."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        print("❌ Kanal nicht gefunden!")
        return
    daten = await lese_google_sheet()
    gesamt = sum(parse_float(d["Wert"]) for d in daten)
    await channel.send(f"📆 **Update:** Gesamtwert: {gesamt:,.2f} €")

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    tages_update.start()

bot.run(DISCORD_TOKEN)
