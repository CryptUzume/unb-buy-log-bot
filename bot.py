import os
import json
import re
from datetime import datetime, timezone, timedelta

import discord
import gspread

# =========================
# 環境変数
# =========================
TOKEN = os.getenv("TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
SHEET_NAME = os.getenv("SHEET_NAME")

if not all([TOKEN, SERVICE_ACCOUNT_JSON, SPREADSHEET_NAME, SHEET_NAME]):
    raise ValueError("必要な環境変数が設定されていません")

# =========================
# 定数
# =========================
TARGET_CHANNEL_ID = 1389281116418211861
JST = timezone(timedelta(hours=9))

# =========================
# Google Sheets
# =========================
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON))
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# =========================
# Discord
# =========================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# ヘルパー
# =========================
def parse_description(desc: str):
    """
    embed.description から必要な情報を抽出
    """
    user_match = re.search(r"\*\*User:\*\*\s*(.+)", desc)
    amount_match = re.search(r"Cash:\s*`?(-?\d+)`?\s*\|\s*Bank:\s*`?(-?\d+)`?", desc)
    reason_match = re.search(r"\*\*Reason:\*\*\s*(.+)", desc)

    user = user_match.group(1).strip() if user_match else ""
    cash = amount_match.group(1) if amount_match else ""
    bank = amount_match.group(2) if amount_match else ""
    reason = reason_match.group(1).strip() if reason_match else ""

    return user, cash, bank, reason

# =========================
# イベント
# =========================
@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

@client.event
async def on_message(message: discord.Message):
    # 対象チャンネルのみ
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # Embed がなければ無視
    if not message.embeds:
        return

    for embed in message.embeds:
        desc = embed.description or ""

        # 🔴 buy ログ以外は全て無視
        if "buy item" not in desc:
            return

        # データ抽出
        user, cash, bank, reason = parse_description(desc)

        # タイムスタンプ（JST）
        timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

        row = [
            timestamp,
            client.user.name,
            "buy",
            user,
            cash,
            bank,
            reason
        ]

        sheet.append_row(row)
        print("スプレッドシートに書き込み:", row)

# =========================
# 起動
# =========================
client.run(TOKEN)

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

bot.run(TOKEN)
