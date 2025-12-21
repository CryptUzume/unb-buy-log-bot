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
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # 既存のシートを使用

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # ユーザー名変換に必須
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現
# =====================
BUY_PATTERN = re.compile(r"buy item", re.IGNORECASE)

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

# =====================
# on_ready
# =====================
@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print("✅ Google Sheets 接続成功")

# =====================
# メッセージ受信時
# =====================
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    # 埋め込みからBUYログを抽出
    if not message.embeds:
        return  # 埋め込みがない場合は無視

    embed = message.embeds[0]
    embed_text = embed.description or ""

    if not BUY_PATTERN.search(embed_text):
        print(f"⏭ BUY 判定できず")
        return

    processed_message_ids.add(message.id)

    # ====== ユーザーID抽出と表示名変換 ======
    user_match = re.search(r"<@!?(\d+)>", embed_text)
    if user_match:
        user_id = int(user_match.group(1))
        member = message.guild.get_member(user_id)
        if member:
            user_name = member.display_name
        else:
            user_name = f"<@{user_id}>"
    else:
        user_name = "Unknown"

    # ====== 金額・理由抽出 ======
    cash_match = re.search(r"Cash:\s*`(-?\d+)`", embed_text)
    bank_match = re.search(r"Bank:\s*`(-?\d+)`", embed_text)
    reason_match = re.search(r"Reason:\s*(.+)", embed_text)

    cash = int(cash_match.group(1)) if cash_match else 0
    bank = int(bank_match.group(1)) if bank_match else 0
    reason = reason_match.group(1).strip() if reason_match else ""

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = client.user.name
    action = "BUY"

    # ====== Railway / ターミナル用ログ ======
    print(f"📝 BUYログ取得:")
    print(f"📩 User: {user_name} | Cash: {cash} | Bank: {bank} | Reason: {reason}")

    # ====== 書き込み ======
    print(f"📝 Sheets に書き込み開始")
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
