import os
import json
import asyncio
import gspread
from discord import Intents
from discord.ext import commands

# =========================
# 環境変数の取得
# =========================
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")
SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME")
SHEET_NAME = os.environ.get("SHEET_NAME")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN が環境変数に設定されていません。")
if not GOOGLE_CREDENTIALS:
    raise ValueError("GOOGLE_CREDENTIALS が環境変数に設定されていません。")
if not SPREADSHEET_NAME or not SHEET_NAME:
    raise ValueError("SPREADSHEET_NAME または SHEET_NAME が設定されていません。")

# =========================
# Google Sheets 認証
# =========================
creds_dict = json.loads(GOOGLE_CREDENTIALS)
gc = gspread.service_account_from_dict(creds_dict)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# =========================
# Discord Bot 設定
# =========================
intents = Intents.default()
intents.message_content = True  # メッセージ取得用
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# Buyログを検知してスプレッドシートに追記
# =========================
@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # ここでBuyログかどうか判定
    if "Buy" in message.content:  # シンプル判定。必要に応じて正規表現に変更可
        # 追記する内容
        row = [message.created_at.isoformat(), message.author.name, message.content]
        sheet.append_row(row)
        print(f"Buyログを追加: {row}")

# =========================
# Bot起動
# =========================
bot.run(DISCORD_TOKEN)
