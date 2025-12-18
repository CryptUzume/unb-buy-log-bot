import os
import discord
from discord.ext import tasks
import gspread
from datetime import datetime
import json

# --- 設定 ---
TOKEN = os.getenv("DISCORD_TOKEN")  # Discord Bot Token
CHANNEL_ID = 123456789012345678     # 監視するチャンネルIDに置き換えてください
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")  # JSONをそのまま環境変数に登録

if not TOKEN:
    raise ValueError("DISCORD_TOKEN が環境変数に設定されていません。")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# --- Google Sheets 接続 ---
sa_info = json.loads(SERVICE_ACCOUNT_JSON)
gc = gspread.service_account_from_dict(sa_info)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# --- Discord クライアント ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} でログ取得開始")

@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    if "Unbilievable boat" in message.content and "Buy" in message.content:
        # --- 時間を日本時間に変換 ---
        now = datetime.utcnow()
        jst = now.replace(hour=(now.hour + 9) % 24)  # UTC→JST
        timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")

        # --- 例: ログ内容を取得（メッセージ全文） ---
        content = message.content

        # --- スプレッドシートに追記 ---
        sheet.append_row([timestamp, content])
        print(f"Logged: {timestamp} - {content}")

bot.run(TOKEN)
