import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
import pytz

TOKEN = os.environ["TOKEN"]
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
SERVICE_ACCOUNT_JSON = os.environ["SERVICE_ACCOUNT_JSON"]

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON))
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Buyログの埋め込み解析
def parse_buy_embed(embed: discord.Embed):
    print("DEBUG EMBED TITLE:", embed.title)
    print("DEBUG EMBED DESCRIPTION:", embed.description)
    data = {}
    if embed.description and "buy item" in embed.description:
        lines = embed.description.split("\n")
        for line in lines:
            if line.startswith("**User:**"):
                data["user"] = line.replace("**User:**", "").strip()
            elif line.startswith("**Amount:**"):
                # Cash と Bank を分ける
                parts = line.replace("**Amount:**", "").strip().split("|")
                for part in parts:
                    key, value = part.split(":")
                    data[key.strip().lower()] = value.strip()
            elif line.startswith("**Reason:**"):
                data["reason"] = line.replace("**Reason:**", "").strip()
            elif line:
                # 最後の行は timestamp として扱う
                data["timestamp"] = line.strip()
        return data
    return None

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id != 1389281116418211861:  # 対象チャンネル
        return

    if message.embeds:
        for embed in message.embeds:
            buy_data = parse_buy_embed(embed)
            if buy_data:
                # 日本時間で timestamp を補正
                try:
                    dt = datetime.strptime(buy_data["timestamp"], "%Y/%m/%d %H:%M")
                    jst = pytz.timezone("Asia/Tokyo")
                    dt = jst.localize(dt)
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    timestamp_str = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")

                row = [
                    timestamp_str,
                    bot.user.name,
                    "Buy",
                    buy_data.get("user", ""),
                    buy_data.get("cash", ""),
                    buy_data.get("bank", ""),
                    buy_data.get("reason", "")
                ]
                print("DEBUG ROW TO SHEET:", row)
                sheet.append_row(row)
