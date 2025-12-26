import os
import json
import re
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

import gspread
from oauth2client.service_account import ServiceAccountCredentials


# =====================
# 設定
# =====================

DISCORD_TOKEN = os.environ["TOKEN"]

SPREADSHEET_ID = "1dW5GQyn2Uc7qtgiCocrtBAgjcJyjNL4zoKexkZXVjbA"
SHEET_NAME = "シート1"

JST = timezone(timedelta(hours=9))


# =====================
# Google Sheets 接続
# =====================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = json.loads(
    os.environ["SERVICE_ACCOUNT_JSON"]
)

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    service_account_info,
    scope
)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

print("✅ Google Sheets 接続成功")


# =====================
# Discord Bot
# =====================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    # Bot 自身は無視
    if message.author.bot is False:
        return

    print(f"📩 message received: {message.id}")

    # ===== 埋め込みのみ対象 =====
    if not message.embeds:
        return

    for embed in message.embeds:
        # タイトルなしは想定内
        description = embed.description
        if not description:
            continue

        # buy item を含まないものは除外
        if "buy item" not in description.lower():
            print("⏭ BUY 判定できず")
            continue

        # ===== 正規表現で抽出 =====
        user_match = re.search(r"\*\*User:\*\*\s*<@(\d+)>", description)
        cash_match = re.search(r"Cash:\s*`(-?\d+)`", description)
        bank_match = re.search(r"Bank:\s*`(-?\d+)`", description)
        reason_match = re.search(r"\*\*Reason:\*\*\s*(.+)", description)

        if not (user_match and cash_match and bank_match and reason_match):
            print("⏭ 必須項目不足")
            continue

        user_id = user_match.group(1)
        cash = cash_match.group(1)
        bank = bank_match.group(1)
        reason = reason_match.group(1).strip()

        # JST タイムスタンプ
        timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

        row = [
            timestamp,
            message.author.name,
            "BUY",
            user_id,
            cash,
            bank,
            reason
        ]

        print(
            f"📝 Sheets に書き込み開始 | "
            f"User: {user_id} | Cash: {cash} | Bank: {bank} | Reason: {reason}"
        )

        sheet.append_row(row, value_input_option="USER_ENTERED")

        print("✅ Sheets 書き込み完了")


# =====================
# 起動
# =====================

bot.run(DISCORD_TOKEN)
