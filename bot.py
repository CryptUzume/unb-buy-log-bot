import os
import json
import discord
import gspread
from datetime import datetime, timezone, timedelta

# 環境変数の取得
TOKEN = os.getenv("TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
CHANNEL_ID = 1389281116418211861

if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# Google認証
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON), scopes=scope)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# 登録済みログを管理して重複防止
logged_messages = set()

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return

    # 埋め込みをチェック
    if not message.embeds:
        return

    embed = message.embeds[0]
    content = embed.description if embed.description else ""
    
    if "Reason: buy item" not in content:
        return

    # 重複チェック
    unique_id = f"{message.id}"
    if unique_id in logged_messages:
        return
    logged_messages.add(unique_id)

    # 内容をスプレッドシート用に整形
    lines = content.split("\n")
    user_line = next((l for l in lines if l.startswith("User:")), "")
    amount_line = next((l for l in lines if l.startswith("Amount:")), "")
    reason_line = next((l for l in lines if l.startswith("Reason:")), "")
    time_line = next((l for l in lines if l), "")  # 最後の時間行

    # 日本時間に変換
    now_jst = datetime.now(timezone(timedelta(hours=9)))
    timestamp = now_jst.strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        user_line.replace("User: ", ""),
        amount_line.replace("Amount: ", ""),
        reason_line.replace("Reason: ", ""),
        time_line
    ]

    sheet.append_row(row)
    print(f"記録しました: {row}")

bot.run(TOKEN)
