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
# Google Sheets 認証
# =====================
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
worksheet = gc.open(SPREADSHEET_NAME).worksheet("シート1")  # 正確なシート名

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現
# =====================
CASH_PATTERN = re.compile(r"Cash: `(-?\d+)`")
BANK_PATTERN = re.compile(r"Bank: `(-?\d+)`")
REASON_PATTERN = re.compile(r"Reason: (.+)")

processed_message_ids = set()

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    processed_message_ids.add(message.id)

    buy_detected = False
    cash = bank = reason = ""

    # メッセージ埋め込みを確認
    if message.embeds:
        for embed in message.embeds:
            text = ""
            if embed.description:
                text += embed.description + "\n"
            for field in embed.fields:
                text += f"{field.name}: {field.value}\n"

            if "buy item" in text.lower():  # Buyログ判定
                buy_detected = True
                cash_match = CASH_PATTERN.search(text)
                bank_match = BANK_PATTERN.search(text)
                reason_match = REASON_PATTERN.search(text)

                cash = cash_match.group(1) if cash_match else ""
                bank = bank_match.group(1) if bank_match else ""
                reason = reason_match.group(1) if reason_match else text.strip()

    if not buy_detected:
        print(f"⏭ BUY 判定できず\n📩 message received: {message.id}")
        return

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = str(message.author)
    user_name = ""  # IDを名前に変換したい場合は後で処理可能

    worksheet.append_row([
        timestamp,
        bot_name,
        "BUY",
        user_name,
        cash,
        bank,
        reason
    ], value_input_option="USER_ENTERED")

    print("✅ Sheets 書き込み完了")

client.run(TOKEN)
