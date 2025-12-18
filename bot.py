import os
import json
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import discord
from discord.ext import commands
from datetime import datetime
import pytz

# ==== 設定 ====
TOKEN = os.getenv("TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Point shop")
SHEET_NAME = os.getenv("SHEET_NAME", "シート1")
TARGET_CHANNEL_ID = 1389281116418211861  # 対象チャンネルID

# ==== Google Sheets 認証 ====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(SERVICE_ACCOUNT_JSON), scope)
gc = gspread.authorize(creds)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ==== Discord Bot 設定 ====
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # 必須
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== 登録済みログ管理 ====
logged_messages = set()

@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id != TARGET_CHANNEL_ID:
        return
    if not message.embeds:
        return

    embed = message.embeds[0]
    desc = embed.description or ""

    if "Balance updated" not in desc:
        return

    # 重複チェック
    if message.id in logged_messages:
        return
    logged_messages.add(message.id)

    # 正規表現で必要な項目を抜き出す
    user_match = re.search(r"User: <@!?(\d+)>", desc)
    amount_match = re.search(r"Cash: ([\-\d]+) \| Bank: ([\-\d]+)", desc)
    reason_match = re.search(r"Reason: (.+)", desc)
    date_match = re.search(r"(\d{1,2})\s+\d{1,2}:\d{2}", desc)

    if user_match and amount_match and reason_match and date_match:
        user_id = user_match.group(1)
        cash = amount_match.group(1)
        bank = amount_match.group(2)
        reason = reason_match.group(1)
        day = date_match.group(1)

        # 日本時間で時刻を取得
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # スプレッドシートに書き込み
        sheet.append_row([time_str, user_id, cash, bank, reason])
        print(f"ログを登録しました: {user_id}, {cash}, {bank}, {reason}, {time_str}")

bot.run(TOKEN)
