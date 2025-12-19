import os
import json
import asyncio
from datetime import datetime, timezone

import discord
import gspread

# =====================
# 環境変数
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY")
SHEET_NAME = os.getenv("SHEET_NAME")

# =====================
# Google Sheets 接続
# =====================
service_account_info = json.loads(SERVICE_ACCOUNT_JSON.replace("\\n", "\n"))
gc = gspread.service_account_from_dict(service_account_info)
sh = gc.open_by_key(SPREADSHEET_KEY)
worksheet = sh.worksheet(SHEET_NAME)

# =====================
# Discord 設定
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # ← ユーザー名取得に必須

client = discord.Client(intents=intents)

# =====================
# Ready
# =====================
@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

# =====================
# メッセージ監視（buyログのみ）
# =====================
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.embeds:
        return

    for embed in message.embeds:
        # buyログ判定（Reason に buy item が含まれるものだけ）
        if not embed.description:
            continue

        if "buy item" not in embed.description.lower():
            continue

        # =====================
        # embed 解析
        # =====================
        user_id = None
        cash = ""
        bank = ""
        reason = ""

        lines = embed.description.split("\n")
        for line in lines:
            if line.startswith("**User:**"):
                user_id = line.split("<@")[1].split(">")[0]

            elif line.startswith("**Amount:**"):
                # Cash: `-5` | Bank: `0`
                parts = line.replace("**Amount:**", "").split("|")
                cash = parts[0].split("`")[1]
                bank = parts[1].split("`")[1]

            elif line.startswith("**Reason:**"):
                reason = line.replace("**Reason:**", "").strip()

        if not user_id:
            return

        # =====================
        # ユーザー名変換
        # =====================
        member = message.guild.get_member(int(user_id))
        if member:
            username = member.display_name
        else:
            username = f"Unknown ({user_id})"

        # =====================
        # 書き込みデータ
        # =====================
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        bot_name = str(client.user)
        action = "BUY"

        row = [
            timestamp,
            bot_name,
            action,
            username,
            cash,
            bank,
            reason
        ]

        # =====================
        # スプレッドシート書き込み
        # =====================
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        print("BUY ログを書き込み:", row)

# =====================
# 起動
# =====================
client.run(TOKEN)
