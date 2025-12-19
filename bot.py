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
worksheet = gc.open(SPREADSHEET_NAME).sheet1

print("✅ Google Sheets 接続成功")

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = False
client = discord.Client(intents=intents)

processed_message_ids = set()

# =====================
# Embed パース
# =====================
def parse_unbelievaboat_buy(embed: discord.Embed):
    user = ""
    cash = ""
    bank = ""
    reason = ""

    for field in embed.fields:
        name = field.name.lower()
        value = field.value

        if "user" in name:
            user = value.strip()

        elif "amount" in name:
            cash_match = re.search(r"Cash:\s*`?(-?\d+)`?", value)
            bank_match = re.search(r"Bank:\s*`?(-?\d+)`?", value)

            if cash_match:
                cash = cash_match.group(1)
            if bank_match:
                bank = bank_match.group(1)

        elif "reason" in name:
            reason = value.strip()

    return user, cash, bank, reason

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    if not message.author.bot:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    user, cash, bank, reason = parse_unbelievaboat_buy(embed)

    # BUY ログでなければ弾く
    if not user or cash == "" or bank == "":
        return

    processed_message_ids.add(message.id)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = message.author.name
    action = "BUY"

    worksheet.append_row(
        [timestamp, bot_name, action, user, cash, bank, reason],
        value_input_option="USER_ENTERED"
    )

    print("✅ BUY ログを Sheets に記録")

client.run(TOKEN)
