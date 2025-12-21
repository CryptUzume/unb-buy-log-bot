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
worksheet = gc.open(SPREADSHEET_NAME).worksheet("シート1")  # 日本語シート名対応

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現（埋め込み）
# =====================
BUY_PATTERN = re.compile(r"buy item", re.IGNORECASE)

# =====================
# JST 設定
# =====================
JST = timezone(timedelta(hours=9))

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print(f"✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    # 埋め込みから BUY ログ判定
    if not message.embeds:
        return

    for embed in message.embeds:
        desc = embed.description
        if not desc or not BUY_PATTERN.search(desc):
            continue

        processed_message_ids.add(message.id)

        # 埋め込みのテキストから情報抽出
        # 例の形式に合わせて正規表現で抽出
        user_match = re.search(r"\*\*User:\*\* <@(\d+)>", desc)
        cash_match = re.search(r"Cash: `(-?\d+)`", desc)
        bank_match = re.search(r"Bank: `(-?\d+)`", desc)
        reason_match = re.search(r"\*\*Reason:\*\* (.+)", desc)

        user_id = user_match.group(1) if user_match else "Unknown"
        user_name = str(message.guild.get_member(int(user_id))) if message.guild.get_member(int(user_id)) else f"<@{user_id}>"
        cash = cash_match.group(1) if cash_match else ""
        bank = bank_match.group(1) if bank_match else
