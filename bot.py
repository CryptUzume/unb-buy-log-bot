import os
import json
import discord
from discord.ext import commands
import gspread
from datetime import datetime
import pytz

# 環境変数から設定
TOKEN = os.environ.get("TOKEN")
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
CHANNEL_ID = 1389281116418211861

if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# Google Sheets 接続
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON), scopes=scope)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 重複チェック用
logged_messages = set()

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    # 対象チャンネルのみ処理
    if message.channel.id != CHANNEL_ID:
        return
    # 埋め込みメッセージのみ
    if not message.embeds:
        return

    embed = message.embeds[0]
    title = embed.title or ""
    description = embed.description or ""

    # Buyログだけ処理
    if "buy item" not in description.lower():
        return

    # 重複防止
    msg_id = f"{message.id}"
    if msg_id in logged_messages:
        return
    logged_messages.add(msg_id)

    # 内容を抽出
    user_line = next((line for line in description.splitlines() if line.startswith("User:")), "")
    amount_line = next((line for line in description.splitlines() if line.startswith("Amount:")), "")
    reason_line = next((line for line in description.splitlines() if line.startswith("Reason:")), "")
    time_line = next((line for line in description.splitlines() if line.startswith("今日")), "")

    # 日本時間に変換
    tz = pytz.timezone("Asia/Tokyo")
    now_jp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    row = [
        now_jp,
        user_line.replace("User: ", "").strip(),
        amount_line.replace("Amount: ", "").strip(),
        reason_line.replace("Reason: ", "").strip(),
        time_line.replace("今日 ", "").strip()
    ]

    # スプレッドシートに追加
    sheet.append_row(row)
    print(f"Logged: {row}")

bot.run(TOKEN)
