import os
import json
import re
from datetime import datetime, timedelta, timezone

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
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # 既存の1つ目のシートを使用

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現（埋め込み専用）
# =====================
EMBED_PATTERN = re.compile(
    r"\*\*User:\*\* <@(\d+)>\s+"
    r"\*\*Amount:\*\* Cash: `(-?\d+)` \| Bank: `(-?\d+)`\s+"
    r"\*\*Reason:\*\* (.+)",
    re.DOTALL
)

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=9))

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print("✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return  # 一般ユーザーは無視

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    processed_message_ids.add(message.id)

    # 埋め込みだけを対象にする
    if not message.embeds:
        print("⏭ BUY 判定できず（埋め込みなし）")
        return

    for embed in message.embeds:
        embed_text = embed.description or ""
        match = EMBED_PATTERN.search(embed_text)
        if not match:
            print(f"⏭ BUY 判定できず\n📩 message received: {message.id}")
            continue

        user_id, cash, bank, reason = match.groups()
        timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        bot_name = client.user.name
        action = "BUY"

        # Google Sheets に書き込み
        print(f"📝 Sheets に書き込み開始\n📩 User: <@{user_id}> | Cash: {cash} | Bank: {bank} | Reason: {reason}")
        worksheet.append_row([
            timestamp,
            bot_name,
            action,
            f"<@{user_id}>",
            cash,
            bank,
            reason
        ], value_input_option="USER_ENTERED")
        print("✅ Sheets 書き込み完了")

client.run(TOKEN)
