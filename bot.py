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

# =====================
# Discord Client
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# BUY 判定用正規表現
# =====================
BUY_PATTERN = re.compile(r"\bbuy\b", re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r"Cash: `(-?\d+)` \| Bank: `(-?\d+)`")
REASON_PATTERN = re.compile(r"buy item \(.+?\)")

# =====================
# 既に処理したメッセージID保持
# =====================
processed_message_ids = set()

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print("✅ Google Sheets 接続成功")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot is False:
        return

    if message.channel.id != BUY_LOG_CHANNEL:
        return

    if message.id in processed_message_ids:
        return

    # 埋め込みがない場合は無視
    if not message.embeds:
        print("⏭ 埋め込みなしのためBUY判定できず")
        return

    embed = message.embeds[0]
    embed_text = embed.description or ""

    # field がある場合は全て結合
    for f in embed.fields:
        embed_text += "\n" + (f.value or "")

    if not BUY_PATTERN.search(embed_text):
        print("⏭ BUY 判定できず")
        return

    processed_message_ids.add(message.id)

    # User抽出
    user_id_match = re.search(r"<@!?(\d+)>", embed_text)
    if user_id_match:
        user_id = int(user_id_match.group(1))
        try:
            user_obj = await client.fetch_user(user_id)
            user_name = str(user_obj)
        except:
            user_name = f"<@{user_id}>"
    else:
        user_name = "Unknown"

    # Cash / Bank 抽出
    cash = bank = 0
    amount_match = AMOUNT_PATTERN.search(embed_text)
    if amount_match:
        cash = int(amount_match.group(1))
        bank = int(amount_match.group(2))

    # Reason 抽出（buy item の部分だけ）
    reason_match = REASON_PATTERN.search(embed_text)
    reason = reason_match.group(0) if reason_match else ""

    # スプレッドシートに書き込み
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = client.user.name
    action = "BUY"

    print(f"📩 User: {user_name} | Cash: {cash} | Bank: {bank} | Reason: {reason}")
    print("📝 Sheets に書き込み開始")

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
