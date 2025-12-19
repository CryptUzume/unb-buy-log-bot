import os
import json
import discord
import gspread
from datetime import datetime
from discord.ext import commands

# =====================
# 環境変数
# =====================
TOKEN = os.getenv("TOKEN")
BUY_LOG_CHANNEL = int(os.getenv("BUY_LOG_CHANNEL"))
SPREADSHEET_NAME = "Point shop"
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# =====================
# Discord 設定
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# Google Sheets 接続
# =====================
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
gc = gspread.service_account_from_dict(creds_dict)
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # 既存シートのみ使用

# =====================
# 起動ログ
# =====================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# =====================
# BUYログ取得
# =====================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    # BUY 以外は無視
    if not message.content.lower().startswith("buy"):
        return

    # ユーザー名取得（表示名優先）
    user_name = (
        message.author.display_name
        if isinstance(message.author, discord.Member)
        else message.author.name
    )

    # ログ解析（想定形式）
    # buy item cash bank reason
    parts = message.content.split(maxsplit=4)

    cash = ""
    bank = ""
    reason = ""

    if len(parts) >= 3:
        cash = parts[2]
    if len(parts) >= 4:
        bank = parts[3]
    if len(parts) == 5:
        reason = parts[4]

    # スプレッドシート追記（ヘッダーなし）
    worksheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        bot.user.name,
        "BUY",
        user_name,
        cash,
        bank,
        reason
    ])

    await bot.process_commands(message)

# =====================
# Bot 起動
# =====================
bot.run(TOKEN)
