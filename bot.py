import os
import json
import re
from datetime import datetime

import discord
import gspread
from google.oauth2.service_account import Credentials

# =====================
# 環境変数
# =====================
TOKEN = os.getenv("TOKEN")
BUY_LOG_CHANNEL = int(os.getenv("BUY_LOG_CHANNEL"))
SPREADSHEET_NAME = "Point shop"
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

if not TOKEN:
    raise RuntimeError("TOKEN が設定されていません")
if not SERVICE_ACCOUNT_JSON:
    raise RuntimeError("SERVICE_ACCOUNT_JSON が設定されていません")

# =====================
# Google Sheets 認証
# =====================
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # タブ名は1つ目固定

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

# =====================
# Buy判定正規表現
# =====================
BUY_PATTERN = re.compile(r"buy item", re.IGNORECASE)
CASH_PATTERN = re.compile(r"Cash:\s*`(-?\d+)`")
BANK_PATTERN = re.compile(r"Bank:\s*`(-?\d+)`")
USER_PATTERN = re.compile(r"\*\*User:\*\*\s*<@!?(\d+)>")
REASON_PATTERN = re.compile(r"\*\*Reason:\*\*\s*(.+)")

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print(f"✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return  # 通常ユーザーのメッセージは無視

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    # 埋め込みメッセージのみ対象
    if not message.embeds:
        return

    for embed in message.embeds:
        desc = embed.description
        if not desc:
            continue

        if not BUY_PATTERN.search(desc):
            continue

        processed_message_ids.add(message.id)

        # User / Cash / Bank / Reason 抜き出し
        user_match = USER_PATTERN.search(desc)
        cash_match = CASH_PATTERN.search(desc)
        bank_match = BANK_PATTERN.search(desc)
        reason_match = REASON_PATTERN.search(desc)

        user_id = user_match[1] if user_match else ""
        cash = int(cash_match[1]) if cash_match else 0
        bank = int(bank_match[1]) if bank_match else 0
        reason = reason_match[1].strip() if reason_match else ""

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        bot_name = client.user.name
        action = "BUY"

        # ログ出力
        print(f"📩 User: <@{user_id}> | Cash: {cash} | Bank: {bank} | Reason: {reason}")
        print("📝 Sheets に書き込み開始")

        # Sheets に書き込み
        worksheet.append_row([
            timestamp,
            bot_name,
            action,
            f"<@{user_id}>",
            cash,
            bank,
            reason
        ], value_input_option="USER_ENTERED")

        print("✅ Sheets 書き込み完了")

client.run(TOKEN)
