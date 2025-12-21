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
worksheet = gc.open(SPREADSHEET_NAME).worksheet("シート1")

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
# 正規表現
# =====================
BUY_PATTERN = re.compile(r"buy item", re.IGNORECASE)
CASH_PATTERN = re.compile(r"Cash:\s*`([-+]?\d+)`")
BANK_PATTERN = re.compile(r"Bank:\s*`([-+]?\d+)`")
REASON_PATTERN = re.compile(r"Reason:\s*(.+)")

def extract_buy_data(embed: discord.Embed):
    """
    UnbelievaBoat の埋め込みからデータ抽出
    """
    text = ""
    for field in embed.fields:
        text += f"**{field.name}:** {field.value}\n"

    cash_match = CASH_PATTERN.search(text)
    bank_match = BANK_PATTERN.search(text)
    reason_match = REASON_PATTERN.search(text)

    cash = cash_match.group(1) if cash_match else ""
    bank = bank_match.group(1) if bank_match else ""
    reason = reason_match.group(1) if reason_match else text.strip()

    # ユーザー情報
    user_match = re.search(r"\*\*User:\*\*\s*<@!?(\d+)>", text)
    user_id = int(user_match.group(1)) if user_match else None

    return user_id, cash, bank, reason, text

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print(f"✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return  # Bot以外は無視
    if message.channel.id != BUY_LOG_CHANNEL:
        return
    if message.id in processed_message_ids:
        return

    # UnbelievaBoat の埋め込みメッセージか確認
    if not message.embeds:
        return

    for embed in message.embeds:
        user_id, cash, bank, reason, full_text = extract_buy_data(embed)
        if not BUY_PATTERN.search(reason):
            print(f"⏭ BUY 判定できず\n📩 message received: {message.id}")
            continue

        processed_message_ids.add(message.id)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        bot_name = message.author.name
        action = "BUY"
        user_name = f"<@{user_id}>" if user_id else ""

        # コンソールログ
        print("🧾 抽出テキスト:")
        print(full_text)
        print(f"✅ Sheets 書き込み開始: {user_name}, Cash={cash}, Bank={bank}, Reason={reason}")

        # Google Sheets に書き込み
        worksheet.append_row([
            timestamp,
            bot_name,
            action,
            user_name,
            cash,
            bank,
            reason
        ], value_input_option="USER_ENTERED")

        print("✅ Sheets 書き込み完了")

client.run(TOKEN)
