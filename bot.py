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
WORKSHEET_NAME = "シート1"
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

# UnbelievaBoat の Bot ID
UNBELIEVABOAT_BOT_ID = 356950275044122625

# =====================
# Google Sheets 認証
# =====================
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)

spreadsheet = gc.open(SPREADSHEET_NAME)
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

print("✅ Google Sheets 接続成功")

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# 正規表現
# =====================
BUY_PATTERN = re.compile(r"buy item", re.IGNORECASE)
CASH_PATTERN = re.compile(r"Cash:\s*`([+-]?[0-9,]+)`")
BANK_PATTERN = re.compile(r"Bank:\s*`([+-]?[0-9,]+)`")
USER_PATTERN = re.compile(r"<@(\d+)>")

processed_message_ids = set()

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    print(f"📩 message received: {message.id}")

    # チャンネル制限
    if message.channel.id != BUY_LOG_CHANNEL:
        return

    # UnbelievaBoat 以外の Bot / User は無視
    if message.author.id != UNBELIEVABOAT_BOT_ID:
        return

    if message.id in processed_message_ids:
        return

    if not message.embeds:
        print("⏭ embed なし")
        return

    processed_message_ids.add(message.id)

    embed = message.embeds[0]

    text = "\n".join(f.value for f in embed.fields)
    print(f"🧾 抽出テキスト:\n{text}")

    if not BUY_PATTERN.search(text):
        print("⏭ BUY 判定できず")
        return

    cash = ""
    bank = ""
    user = ""

    if m := CASH_PATTERN.search(text):
        cash = m.group(1).replace(",", "")
    if m := BANK_PATTERN.search(text):
        bank = m.group(1).replace(",", "")
    if m := USER_PATTERN.search(text):
        user = m.group(1)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    worksheet.append_row([
        timestamp,
        message.author.name,
        "BUY",
        user,
        cash,
        bank,
        text
    ], value_input_option="USER_ENTERED")

    print("✅ Sheets 書き込み完了")

client.run(TOKEN)
