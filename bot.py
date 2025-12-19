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
# Google Sheets
# =====================
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
worksheet = gc.open(SPREADSHEET_NAME).sheet1

print("✅ Google Sheets 接続成功")

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True  # 念のため有効化
client = discord.Client(intents=intents)

processed_message_ids = set()

# =====================
# BUY ログ抽出（Embed / Content 両対応）
# =====================
def extract_text(message: discord.Message) -> str:
    if message.embeds:
        embed = message.embeds[0]
        if embed.description:
            return embed.description
        if embed.fields:
            return "\n".join(f.value for f in embed.fields)

    if message.content:
        return message.content

    return ""

def parse_buy(text: str):
    user = re.search(r"\*\*User:\*\*\s*(.+)", text)
    cash = re.search(r"Cash:\s*`?(-?\d+)`?", text)
    bank = re.search(r"Bank:\s*`?(-?\d+)`?", text)
    reason = re.search(r"\*\*Reason:\*\*\s*(.+)", text)

    if not (user and cash and bank):
        return None

    return (
        user.group(1).strip(),
        cash.group(1),
        bank.group(1),
        reason.group(1).strip() if reason else ""
    )

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    print(f"📩 message received: {message.id}")

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    if not message.author.bot:
        return

    text = extract_text(message)
    print("🧾 抽出テキスト:", text)

    result = parse_buy(text)
    if not result:
        print("⏭ BUY 判定できず")
        return

    processed_message_ids.add(message.id)

    user, cash, bank, reason = result

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = message.author.name
    action = "BUY"

    worksheet.append_row(
        [timestamp, bot_name, action, user, cash, bank, reason],
        value_input_option="USER_ENTERED"
    )

    print("✅ Sheets 書き込み完了")

client.run(TOKEN)
