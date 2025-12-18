import os
import json
import discord
from discord.ext import commands
import gspread
from datetime import datetime
import pytz

# ====== 環境変数 ======
TOKEN = os.environ["TOKEN"]  # Discord Bot Token
SERVICE_ACCOUNT_JSON = os.environ["SERVICE_ACCOUNT_JSON"]  # JSON文字列
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
TARGET_CHANNEL_ID = 1389281116418211861  # Buyログチャンネル

# ====== Google Sheets 認証 ======
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gc = gspread.service_account_from_dict(
    json.loads(SERVICE_ACCOUNT_JSON),
    scopes=scope
)

sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ====== Discord Bot ======
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # 埋め込み含むメッセージの取得に必要

bot = commands.Bot(command_prefix="!", intents=intents)

# 重複チェック用
logged_ids = set()

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    # 自分自身のメッセージは無視
    if message.author.bot:
        return

    # 対象チャンネルのみ
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # 埋め込みメッセージのみ処理
    if not message.embeds:
        return

    embed = message.embeds[0]

    # Buyログだけ抽出
    if "buy item" not in embed.description.lower():
        return

    # 重複防止
    if message.id in logged_ids:
        return
    logged_ids.add(message.id)

    # 情報抽出
    user_line = next((line for line in embed.description.split("\n") if line.startswith("User:")), "")
    amount_line = next((line for line in embed.description.split("\n") if line.startswith("Amount:")), "")
    reason_line = next((line for line in embed.description.split("\n") if line.startswith("Reason:")), "")
    time_line = next((line for line in embed.description.split("\n") if "今日" in line or "昨日" in line or "20" in line), "")

    # 日本時間に変換
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst)
    timestamp = now_jst.strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        user_line.replace("User: ", ""),
        amount_line.replace("Amount: ", ""),
        reason_line.replace("Reason: ", ""),
        time_line
    ]

    # スプレッドシートに追加
    try:
        sheet.append_row(row)
        print(f"ログ記録: {row}")
    except Exception as e:
        print(f"スプレシートへの記録エラー: {e}")

bot.run(TOKEN)
