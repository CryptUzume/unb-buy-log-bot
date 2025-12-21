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
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # シート名が「シート1」の場合

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
# 埋め込み Buy 判定用正規表現
# =====================
BUY_REASON_PATTERN = re.compile(r"buy item", re.IGNORECASE)
CASH_PATTERN = re.compile(r"Cash:\s*`([-\d,]+)`")
BANK_PATTERN = re.compile(r"Bank:\s*`([-\d,]+)`")
USER_PATTERN = re.compile(r"\<\@(\d+)\>")  # <@UserID> からID抽出

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print("✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return  # ユーザー発言は無視

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    # 埋め込みがない場合は無視
    if not message.embeds:
        return

    for embed in message.embeds:
        desc = embed.description or ""
        if not BUY_REASON_PATTERN.search(desc):
            continue  # buy item 以外は無視

        # IDをユーザー名に変換（後で実装予定）
        user_match = USER_PATTERN.search(desc)
        user_name = f"<@{user_match[1]}>" if user_match else str(message.author)

        cash_match = CASH_PATTERN.search(desc)
        bank_match = BANK_PATTERN.search(desc)
        cash = cash_match[1] if cash_match else ""
        bank = bank_match[1] if bank_match else ""

        reason_line = [line for line in desc.splitlines() if line.lower().startswith("reason:")]
        reason = reason_line[0].replace("Reason:", "").strip() if reason_line else desc

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        bot_name = client.user.name
        action = "BUY"

        processed_message_ids.add(message.id)

        # シートに書き込み
        worksheet.append_row([
            timestamp,
            bot_name,
            action,
            user_name,
            cash,
            bank,
            reason
        ], value_input_option="USER_ENTERED")

        # ログ出力
        print("📝 Sheets に書き込み開始")
        print(f"📩 User: {user_name} | Cash: {cash} | Bank: {bank} | Reason: {reason}")
        print("✅ Sheets 書き込み完了")

client.run(TOKEN)

