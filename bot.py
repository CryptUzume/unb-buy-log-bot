import os
import discord
from discord.ext import commands
import gspread
from datetime import datetime, timezone, timedelta
import json

# ==== 環境変数 ====
TOKEN = os.environ["TOKEN"]
SERVICE_ACCOUNT_JSON = os.environ["SERVICE_ACCOUNT_JSON"]
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
CHANNEL_ID = 1389281116418211861

# ==== Google Sheets 認証 ====
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON), scopes=scope)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ==== Discord Bot 初期化 ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 重複防止用
logged_messages = set()

# ==== メッセージ監視 ====
@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    if not message.embeds:
        return

    embed = message.embeds[0]

    # 埋め込み本文を取得
    if embed.description:
        content = embed.description
    elif embed.fields:
        content = "\n".join(f"{f.name}: {f.value}" for f in embed.fields)
    else:
        return

    # Buyログだけを抽出
    if "Reason: buy item" not in content:
        return

    # 重複チェック
    unique_id = str(message.id)
    if unique_id in logged_messages:
        return
    logged_messages.add(unique_id)

    # 各項目を抽出
    lines = content.split("\n")
    user_line = next((l for l in lines if l.startswith("User:")), "")
    amount_line = next((l for l in lines if l.startswith("Amount:")), "")
    reason_line = next((l for l in lines if l.startswith("Reason:")), "")
    time_line = lines[-1] if lines else ""

    # JSTタイムスタンプ
    now_jst = datetime.now(timezone(timedelta(hours=9)))
    timestamp = now_jst.strftime("%Y-%m-%d %H:%M:%S")

    # スプレッドシートに追加
    row = [
        timestamp,
        user_line.replace("User: ", ""),
        amount_line.replace("Amount: ", ""),
        reason_line.replace("Reason: ", ""),
        time_line
    ]
    sheet.append_row(row)
    print(f"記録しました: {row}")

# ==== Bot 起動 ====
@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

bot.run(TOKEN)

