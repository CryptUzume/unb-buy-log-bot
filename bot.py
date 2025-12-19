import os
import json
import re
from datetime import datetime

import discord
import gspread
from google.oauth2.service_account import Credentials

# =====================
# 環境変数
# =====================
TOKEN = os.getenv("TOKEN")
BUY_LOG_CHANNEL = int(os.getenv("BUY_LOG_CHANNEL"))
SPREADSHEET_NAME = "Point shop"
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

if not TOKEN:
    raise RuntimeError("TOKEN が設定されていません")
if not SERVICE_ACCOUNT_JSON:
    raise RuntimeError("SERVICE_ACCOUNT_JSON が設定されていません")

# =====================
# Google Sheets
# =====================
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
worksheet = gc.open(SPREADSHEET_NAME).sheet1

print("✅ Google Sheets 接続成功")

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

processed_message_ids = set()

# =====================
# UnbelievaBoat BUY パース
# =====================
def parse_buy_from_embed(embed: discord.Embed):
    text = ""

    if embed.description:
        text = embed.description
    elif embed.fields:
        text = "\n".join(f.value for f in embed.fields)

    if not text:
        return None

    user_match = re.search(r"\*\*User:\*\*\s*(.+)", text)
    cash_match = re.search(r"Cash:\s*`?(-?\d+)`?", text)
    bank_match = re.search(r"Bank:\s*`?(-?\d+)`?", text)
    reason_match = re.search(r"\*\*Reason:\*\*\s*(.+)", text)

    if not (user_match and cash_match and bank_match):
        return None

    user = user_match.group(1).strip()
    cash = cash_match.group(1)
    bank = bank_match.group(1)
    reason = reason_match.group(1).strip() if reason_match else ""

    return user, cash, bank, reason

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    if not message.author.bot:
        return

    if not message.embeds:
        return

    result = parse_buy_from_embed(message.embeds[0])
    if not result:
        return

    processed_message_ids.add(message.id)

    user, cash, bank, reason = result

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = message.author.name
    action = "BUY"

    worksheet.append_row(
        [timestamp, bot_name, action, user, cash, bank, reason],
        value_input_option="USER_ENTERED"
    )

    print("✅ BUY ログを Sheets に記録")

client.run(TOKEN)
