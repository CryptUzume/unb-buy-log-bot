import os
import json
import re
from datetime import datetime

import discord
import gspread
from google.oauth2.service_account import Credentials

# =====================
# 環境変数（変更禁止）
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

worksheet = gc.open(SPREADSHEET_NAME).sheet1
print("✅ Google Sheets 接続成功")

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定（緩和）
# =====================
BUY_PATTERN = re.compile(r"buy", re.IGNORECASE)

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    print(f"📩 Message received: {message.content}")

    if not BUY_PATTERN.search(message.content):
        print("⏭ BUY 判定に該当せず")
        return

    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        bot_name = client.user.name
        action = "BUY"
        user_name = str(message.author)
        cash = ""
        bank = ""
        reason = message.content

        print("📝 Sheets に書き込み開始")

        worksheet.append_row(
            [timestamp, bot_name, action, user_name, cash, bank, reason],
            value_input_option="USER_ENTERED"
        )

        print("✅ Sheets 書き込み完了")

    except Exception as e:
        print("❌ Sheets 書き込み失敗")
        print(e)

client.run(TOKEN)
