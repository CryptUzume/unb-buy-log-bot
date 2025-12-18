import os
import json
import discord
from discord import Intents
from discord.ext import commands
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo  # pytz不要、標準ライブラリ

# 環境変数から設定を取得
TOKEN = os.getenv("TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
TARGET_CHANNEL_ID = 1389281116418211861

if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# Discord Botセットアップ
intents = Intents.default()
intents.message_content = True  # 埋め込み取得に必須
bot = commands.Bot(command_prefix="!", intents=intents)

# Google Sheets認証
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON), scope)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# 登録済みログID管理（重複防止）
logged_messages = set(sheet.col_values(1))  # 1列目にメッセージIDを記録

def parse_buy_embed(embed: discord.Embed):
    """埋め込みからBuyログ情報を抽出"""
    if not embed.title or "Balance updated" not in embed.title:
        return None
    data = {}
    for field in embed.fields:
        name = field.name.lower()
        if "user" in name:
            data["user"] = field.value
        elif "amount" in name:
            data["amount"] = field.value
        elif "reason" in name:
            data["reason"] = field.value
    # タイムスタンプを日本時間に変換
    timestamp = embed.timestamp or datetime.utcnow()
    jst = ZoneInfo("Asia/Tokyo")
    data["timestamp"] = timestamp.astimezone(jst).strftime("%Y-%m-%d %H:%M:%S")
    return data

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id != TARGET_CHANNEL_ID:
        return
    if not message.embeds:
        return
    for embed in message.embeds:
        data = parse_buy_embed(embed)
        if data is None:
            continue
        # 重複チェック（メッセージID）
        if str(message.id) in logged_messages:
            continue
        # スプレッドシートに書き込み
        sheet.append_row([message.id, data["user"], data["amount"], data["reason"], data["timestamp"]])
        logged_messages.add(str(message.id))
        print(f"記録しました: {data}")

bot.run(TOKEN)
