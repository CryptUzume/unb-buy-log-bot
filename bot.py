import os
import json
import base64
import asyncio
import discord
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# 環境変数
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_JSON_BASE64 = os.getenv("SERVICE_ACCOUNT_JSON_BASE64")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID is not set")

if not SERVICE_ACCOUNT_JSON_BASE64:
    raise RuntimeError("SERVICE_ACCOUNT_JSON_BASE64 is not set")

# =========================
# Google Sheets 認証
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_worksheet():
    info = json.loads(
        base64.b64decode(SERVICE_ACCOUNT_JSON_BASE64).decode("utf-8")
    )
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.sheet1  # 1枚目を使用

worksheet = get_worksheet()

# =========================
# Discord Bot 設定
# =========================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# Bot 起動
# =========================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    # 起動確認用ログ
    worksheet.append_row([
        datetime.utcnow().isoformat(),
        "SYSTEM",
        "Bot started"
    ])

# =========================
# メッセージ監視（Buyログ想定）
# =========================
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content

    # 🔽 ここを Buy ログ条件に合わせて調整
    if "BUY" in content.upper():
        try:
            worksheet.append_row([
                datetime.utcnow().isoformat(),
                message.author.name,
                content
            ])
            print("Buy log written to sheet")

        except Exception as e:
            print("Failed to write to sheet:", e)

# =========================
# 実行
# =========================
client.run(DISCORD_TOKEN)
