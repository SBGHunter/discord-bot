import os
import io
import csv
import aiohttp
import discord
from discord.ext import commands, tasks

# --- 🔧 Konfiguration ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
GOOGLE_SHEET_CSV_URL = os.environ.get("GOOGLE_SHEET_CSV_URL")

# --- 🤖 Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


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
                    print(f"❌ Fehler beim Abrufen des CSV: HTTP {resp.status}")
                    return []
                text = await resp.text()
        reader = csv.DictReader(io.StringIO(text))
        daten = [row for row in reader]
        print(f"✅ Google Sheet geladen mit {len(daten)} Zeilen.")
        return daten
    except Exception as e:
        print(f"❌ Fehler beim Lesen des Google Sheets: {e}")
        return []


# --- 💬 Command: !depot ---
@bot.command()
async def depot(ctx):
    """Zeigt das aktuelle Depot in einem Discord-Embed an."""
    daten = await lese_google_sheet()
    if not daten:
        await ctx.send("❌ Keine Daten verfügbar!")
        return

    gesamt = sum(parse_float(d.get("Wert", "0")) for d in daten)

    embed = discord.Embed(
        title="📊 Depotübersicht",
        description=f"💰 **Gesamtwert:** {gesamt:,.2f} €",
        color=discord.Color.green()
    )

    for d in daten:
        aktie = d.get("Aktie", "Unbekannt")
        wert = parse_float(d.get("Wert", "0"))
        veraenderung = parse_float(d.get("Veränderung", "0"))
        emoji = "📈" if veraenderung > 0 else ("📉" if veraenderung < 0 else "➖")

        embed.add_field(
            name=f"{emoji} {aktie}",
            value=f"{wert:,.2f} € ({veraenderung:+.2f}%)",
            inline=False
        )

    await ctx.send(embed=embed)


# --- 🔁 Automatisches Depot-Update ---
@tasks.loop(minutes=10)
async def tages_update():
    """Postet alle 10 Minuten eine neue Depot-Nachricht."""
    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            print(f"❌ Kanal mit ID {DISCORD_CHANNEL_ID} nicht gefunden!")
            return

        daten = await lese_google_sheet()
        if not daten:
            print("❌ Keine Daten für Tages-Update!")
            return

        # Debug-Ausgabe für Render-Logs
        print("🧾 Spalten im CSV:", daten[0].keys())

        gesamt = sum(parse_float(d.get("Wert", "0")) for d in daten)

        embed = discord.Embed(
            title="📆 Depot-Update",
            description=f"💰 **Gesamtwert:** {gesamt:,.2f} €",
            color=discord.Color.blue()
        )

        for d in daten:
            aktie = d.get("Aktie", "Unbekannt")
            wert = parse_float(d.get("Wert", "0"))
            veraenderung = parse_float(d.get("Veränderung", "0"))
            emoji = "📈" if veraenderung > 0 else ("📉" if veraenderung < 0 else "➖")

            embed.add_field(
                name=f"{emoji} {aktie}",
                value=f"{wert:,.2f} € ({veraenderung:+.2f}%)",
                inline=False
            )

        await channel.send(embed=embed)
        print("📤 Depot-Update erfolgreich an Discord gesendet.")

    except Exception as e:
        import traceback
        print("❌ Fehler im tages_update:")
        traceback.print_exc()


# --- ⚙️ Start ---
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    print(f"📡 Sende Updates an Kanal-ID: {DISCORD_CHANNEL_ID}")
    tages_update.start()


bot.run(DISCORD_TOKEN)
