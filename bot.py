import os
import json
from datetime import datetime, timezone, timedelta
import discord
from discord import Intents
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- 設定 ----------
TOKEN = os.environ["TOKEN"]
CHANNEL_ID = 1389281116418211861
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"

# Google Sheets 認証
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# Discord クライアント
intents = Intents.default()
intents.message_content = True
intents.messages = True
client = discord.Client(intents=intents)

# 記録済みログIDを保持
logged_messages = set(sheet.col_values(1))  # 1列目にメッセージIDを保存しておく

# JST時間取得
def get_jst_now():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    jst_now = utc_now + timedelta(hours=9)
    return jst_now.strftime("%Y-%m-%d %H:%M:%S")

# ログ解析
def parse_embed(embed):
    if not embed or "Balance updated" not in embed.title:
        return None
    data = {}
    for field in embed.fields:
        if field.name == "User":
            data["user"] = field.value
        elif field.name == "Amount":
            data["amount"] = field.value
        elif field.name == "Reason":
            data["reason"] = field.value
    return data if "user" in data else None

@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    if not message.embeds:
        return
    
    embed = message.embeds[0]
    log_data = parse_embed(embed)
    if not log_data:
        return

    # 重複チェック
    if str(message.id) in logged_messages:
        return
    
    # スプレッドシートに追加
    row = [str(message.id), log_data["user"], log_data["amount"], log_data["reason"], get_jst_now()]
    sheet.append_row(row)
    logged_messages.add(str(message.id))
    print(f"ログ記録: {row}")

client.run(TOKEN)
