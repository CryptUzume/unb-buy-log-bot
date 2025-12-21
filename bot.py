import os
import json
import re
from datetime import datetime, timedelta

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
worksheet = gc.open(SPREADSHEET_NAME).worksheet("シート1")

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現
# =====================
BUY_PATTERN = re.compile(r"buy item", re.IGNORECASE)
USER_PATTERN = re.compile(r"\*\*User:\*\* <@(\d+)>")
CASH_PATTERN = re.compile(r"Cash: `(-?\d+)`")
BANK_PATTERN = re.compile(r"Bank: `(-?\d+)`")
REASON_PATTERN = re.compile(r"Reason: (.+)")

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print("✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        # Botメッセージのみ処理（埋め込みBuyログ）
        if not message.embeds:
            return
    else:
        # 人間のメッセージは無視
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    for embed in message.embeds:
        embed_text = embed.description or ""
        if not BUY_PATTERN.search(embed_text):
            continue

        processed_message_ids.add(message.id)

        # ======== 抽出 ========
        user_match = USER_PATTERN.search(embed_text)
        cash_match = CASH_PATTERN.search(embed_text)
        bank_match = BANK_PATTERN.search(embed_text)
        reason_match = REASON_PATTERN.search(embed_text)

        user_id = user_match.group(1) if user_match else "Unknown"
        user_obj = message.guild.get_member(int(user_id)) if message.guild else None
        user_name = str(user_obj) if user_obj else f"<@{user_id}>"
        cash = cash_match.group(1) if cash_match else ""
        bank = bank_match.group(1) if bank_match else ""
        reason = reason_match.group(1) if reason_match else ""

        # 日本時間で timestamp
        timestamp = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
        bot_name = client.user.name
        action = "BUY"

        print(f"📩 User: {user_name} | Cash: {cash} | Bank: {bank} | Reason: {reason}")
        print("📝 Sheets に書き込み開始")

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
