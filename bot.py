import os
import json
import discord
import gspread
from discord.ext import commands
from datetime import datetime, timezone, timedelta

# -----------------------------
# 環境変数
# -----------------------------
TOKEN = os.environ.get("TOKEN")
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
LOG_CHANNEL_ID = 1389281116418211861  # Buyログが流れるチャンネル

if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# -----------------------------
# Google スプレッドシート準備
# -----------------------------
# JSON を辞書に変換
service_account_info = json.loads(SERVICE_ACCOUNT_JSON)

# スコープ追加
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

gc = gspread.service_account_from_dict(service_account_info, scopes=scope)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# -----------------------------
# Discord Bot 設定
# -----------------------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # contentを取得する場合必要
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# ヘルパー関数
# -----------------------------
def append_buy_log_to_sheet(message):
    """
    Buyログをシートに追記
    """
    # 日本時間
    JST = timezone(timedelta(hours=+9))
    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    
    # メッセージ内容
    content = message.content

    # ここで必要な情報だけ取り出す場合、正規表現などで加工可
    # 今は内容そのまま記録
    sheet.append_row([now_jst, content])

# -----------------------------
# イベント
# -----------------------------
@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    # Bot 自身のメッセージは無視
    if message.author.bot:
        return

    # 対象チャンネルのみ
    if message.channel.id != LOG_CHANNEL_ID:
        return

    # Buy ログだけ
    if "Buy" in message.content:
        append_buy_log_to_sheet(message)

# -----------------------------
# Bot 起動
# -----------------------------
bot.run(TOKEN)
