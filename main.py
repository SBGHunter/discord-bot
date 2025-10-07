import os
import io
import csv
import aiohttp
import logging
import discord
from discord.ext import commands, tasks
from datetime import datetime

# --- 🔧 Konfiguration ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
GOOGLE_SHEET_CSV_URL = os.environ.get("GOOGLE_SHEET_CSV_URL")

# --- 🧠 Setup Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- 🤖 Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MAX_FIELDS = 25  # Discord erlaubt max. 25 Felder pro Embed


# --- 🧮 Hilfsfunktionen ---
def parse_float(s):
    """Konvertiert einen String mit Komma als Dezimaltrennzeichen zu float."""
    try:
        return float(str(s).replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


async def lese_google_sheet():
    """Liest das Google Sheet (CSV) aus und gibt eine Liste von Dicts zurück."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GOOGLE_SHEET_CSV_URL) as resp:
                if resp.status != 200:
                    logging.error(f"Fehler beim Abrufen des CSV: HTTP {resp.status}")
                    return []
                text = await resp.text()
        reader = csv.DictReader(io.StringIO(text))
        daten = [row for row in reader]
        logging.info(f"Google Sheet geladen mit {len(daten)} Zeilen.")
        return daten
    except Exception as e:
        logging.exception(f"Fehler beim Lesen des Google Sheets: {e}")
        return []


def erstelle_embeds(daten, titel, farbe):
    """Erstellt eine Liste von Embeds mit jeweils max. 25 Feldern."""
    embeds = []
    gesamt = sum(parse_float(d.get("Wert", "0")) for d in daten)

    for i in range(0, len(daten), MAX_FIELDS):
        teil = daten[i:i + MAX_FIELDS]

        embed = discord.Embed(
            title=f"{titel} (Teil {i // MAX_FIELDS + 1})",
            description=f"💰 **Gesamtwert:** {gesamt:,.2f} €",
            color=farbe
        )

        for d in teil:
            aktie = d.get("Aktie", "Unbekannt")
            wert = parse_float(d.get("Wert", "0"))
            veraenderung = parse_float(d.get("Veränderung", "0"))
            emoji = "📈" if veraenderung > 0 else ("📉" if veraenderung < 0 else "➖")

            embed.add_field(
                name=f"{emoji} {aktie}",
                value=f"{wert:,.2f} € ({veraenderung:+.2f}%)",
                inline=False
            )

        embed.set_footer(text=f"Letztes Update: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        embeds.append(embed)

    return embeds


# --- 💬 Command: !depot ---
@bot.command()
async def depot(ctx):
    """Zeigt das aktuelle Depot in Discord an."""
    daten = await lese_google_sheet()
    if not daten:
        await ctx.send("❌ Keine Daten verfügbar!")
        return

    embeds = erstelle_embeds(daten, "📊 Depotübersicht", discord.Color.green())

    for embed in embeds:
        await ctx.send(embed=embed)


# --- 🔁 Automatisches Depot-Update ---
@tasks.loop(minutes=10)
async def tages_update():
    """Postet alle 10 Minuten eine Depot-Aktualisierung."""
    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            logging.error(f"Kanal mit ID {DISCORD_CHANNEL_ID} nicht gefunden!")
            return

        daten = await lese_google_sheet()
        if not daten:
            logging.warning("Keine Daten für Tages-Update!")
            return

        embeds = erstelle_embeds(daten, "📆 Depot-Update", discord.Color.blue())

        for embed in embeds:
            await channel.send(embed=embed)

        logging.info("Depot-Update erfolgreich an Discord gesendet.")

    except Exception as e:
        logging.exception("Fehler im tages_update:")


# --- ⚙️ Start ---
@bot.event
async def on_ready():
    logging.info(f"Bot online als {bot.user}")
    logging.info(f"Sende Updates an Kanal-ID: {DISCORD_CHANNEL_ID}")
    if not tages_update.is_running():
        tages_update.start()


# --- 🚀 Bot starten ---
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_CHANNEL_ID == 0 or not GOOGLE_SHEET_CSV_URL:
        logging.error("Fehlende Environment Variablen! Bitte DISCORD_TOKEN, DISCORD_CHANNEL_ID und GOOGLE_SHEET_CSV_URL setzen.")
    else:
        bot.run(DISCORD_TOKEN)
