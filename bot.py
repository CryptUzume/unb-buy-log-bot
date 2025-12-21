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
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # シート名は「シート1」でも sheet1 で OK

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現（例）
# =====================
BUY_PATTERN = re.compile(r"\bbuy\b", re.IGNORECASE)

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    # =====================
    # BUY 判定（コンテンツ or 埋め込み）
    # =====================
    buy_detected = False

    # message.content をチェック
    if message.content and BUY_PATTERN.search(message.content):
        buy_detected = True

    # 埋め込みをチェック
    if not buy_detected and message.embeds:
        for embed in message.embeds:
            if embed.description and BUY_PATTERN.search(embed.description):
                buy_detected = True
                break
            for field in embed.fields:
                if BUY_PATTERN.search(field.value):
                    buy_detected = True
                    break
            if buy_detected:
                break

    if not buy_detected:
        print(f"⏭ BUY 判定できず\n📩 message received: {message.id}")
        return

    processed_message_ids.add(message.id)

    # =====================
    # 埋め込み情報を抽出
    # =====================
    reason = message.content
    cash = ""
    bank = ""

    if message.embeds:
        for embed in message.embeds:
            if embed.description:
                reason = embed.description
            elif embed.fields:
                reason = "\n".join(f"{f.name}: {f.value}" for f in embed.fields)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = client.user.name
    action = "BUY"
    user_name = str(message.author)

    print(f"📝 Sheets に書き込み開始: {user_name} / {reason}")

    # =====================
    # Sheets 書き込み
    # =====================
    worksheet.append_row([
        timestamp,
        bot_name,
        action,
        user_name,
        cash,
        bank,
        reason
    ], value_input_option="USER_ENTERED")

    print("✅ Sheets 書き込み完了")

client.run(TOKEN)
