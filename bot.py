import os
import asyncio
import discord
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 環境変数から取得
TOKEN = os.getenv("TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
BUY_LOG_CHANNEL = int(os.getenv("BUY_LOG_CHANNEL"))

SPREADSHEET_NAME = "Point shop"

# Google Sheets 認証
import json
credentials_dict = json.loads(SERVICE_ACCOUNT_JSON)
credentials = Credentials.from_service_account_info(credentials_dict)
gc = gspread.authorize(credentials)
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # 既存シートを使用

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # ユーザー情報取得に必要

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

@client.event
async def on_message(message):
    if message.channel.id != BUY_LOG_CHANNEL:
        return

    # buy ログ判定
    if not message.embeds:
        return
    embed = message.embeds[0]
    if embed.title and "buy" not in embed.title.lower():
        return

    # ユーザーID → 名前変換
    user_mention = None
    cash = bank = reason = ""
    try:
        description = embed.description or ""
        for line in description.split("\n"):
            if line.startswith("**User:**"):
                user_mention = line.split(":")[1].strip()
            elif line.startswith("**Amount:**"):
                parts = line.split("|")
                cash = parts[0].replace("Cash:", "").strip(" `")
                bank = parts[1].replace("Bank:", "").strip(" `")
            elif line.startswith("**Reason:**"):
                reason = line.split(":")[1].strip()
    except Exception as e:
        print("DEBUG: Embed parsing error:", e)
        return

    # ユーザー名に変換
    user_name = user_mention
    if user_mention:
        if user_mention.startswith("<@") and user_mention.endswith(">"):
            user_id = int(user_mention.replace("<@", "").replace("!", "").replace(">", ""))
            member = message.guild.get_member(user_id)
            if member:
                user_name = member.name

    # スプレッドシートに追記
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [now, client.user.name, "buy", user_name, cash, bank, reason]
    try:
        worksheet.append_row(row)
        print("スプレッドシートに書き込み完了:", row)
    except Exception as e:
        print("スプレッドシート書き込みエラー:", e)

client.run(TOKEN)
