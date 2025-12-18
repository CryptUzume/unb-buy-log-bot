import os
import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone, timedelta

# ===== 環境変数から読み込み =====
TOKEN = os.environ.get("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN が環境変数に設定されていません。")

SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")
if SERVICE_ACCOUNT_JSON is None:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# ===== スプレッドシート設定 =====
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"

# ===== Discord クライアント =====
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# ===== Google Sheets 接続 =====
scope = ['https://www.googleapis.com/auth/spreadsheets']
credentials_dict = None

import json
try:
    credentials_dict = json.loads(SERVICE_ACCOUNT_JSON)
except Exception as e:
    raise ValueError(f"SERVICE_ACCOUNT_JSON が正しいJSON形式ではありません: {e}")

credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ===== ヘルパー: 日本時間取得 =====
JST = timezone(timedelta(hours=+9))
def now_jst():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

# ===== メッセージ受信時処理 =====
TARGET_CHANNEL_ID = 1389281116418211861

@client.event
async def on_ready():
    print(f"{client.user} が起動しました。")

@client.event
async def on_message(message):
    # 自分のメッセージは無視
    if message.author == client.user:
        return

    # 対象チャンネルか確認
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # Buy ログのみ処理
    if "Buy" in message.content:
        timestamp = now_jst()
        user = str(message.author)
        content = message.content

        # スプレッドシートに追加
        try:
            sheet.append_row([timestamp, user, content])
            print(f"[{timestamp}] Buyログを記録: {user} - {content}")
        except Exception as e:
            print(f"スプレッドシートへの書き込みに失敗: {e}")

# ===== Bot 起動 =====
client.run(TOKEN)
