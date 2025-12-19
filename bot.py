import os
import json
import asyncio
from datetime import datetime, timezone

import discord
import gspread

# =========================
# 環境変数
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "buy-log")
SHEET_NAME = os.getenv("SHEET_NAME", "log")

# UnbelievaBoat の buy ログが流れるチャンネルID（必須）
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))

# =========================
# Google Sheets
# =========================
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON))
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# =========================
# Discord
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

# =========================
# ユーティリティ
# =========================
def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def extract_buy_data(embed: discord.Embed):
    """
    UnbelievaBoat の buy embed から必要な情報だけ抜き出す
    """
    if not embed.description:
        return None

    desc = embed.description

    # buyログ以外は弾く
    if "buy item" not in desc.lower():
        return None

    user_id = None
    cash = ""
    bank = ""
    reason = ""

    lines = desc.splitlines()
    for line in lines:
        if line.startswith("**User:**"):
            # <@123456789>
            user_id = line.split("<@")[1].split(">")[0]
        elif line.startswith("**Amount:**"):
            # Cash: `-5` | Bank: `0`
            parts = line.replace("**Amount:**", "").split("|")
            for p in parts:
                if "Cash" in p:
                    cash = p.split("`")[1]
                if "Bank" in p:
                    bank = p.split("`")[1]
        elif line.startswith("**Reason:**"):
            reason = line.replace("**Reason:**", "").strip()

    if not user_id:
        return None

    return user_id, cash, bank, reason

async def resolve_username(guild: discord.Guild, user_id: str):
    member = guild.get_member(int(user_id))
    if member:
        return f"{member.display_name}"
    try:
        user = await client.fetch_user(int(user_id))
        return f"{user.name}"
    except:
        return user_id  # 最悪ID

# =========================
# イベント
# =========================
@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

@client.event
async def on_message(message: discord.Message):
    # 対象チャンネルのみ
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # Bot自身 or embed無しは無視
    if not message.embeds:
        return

    embed = message.embeds[0]
    data = extract_buy_data(embed)
    if not data:
        return

    user_id, cash, bank, reason = data
    username = await resolve_username(message.guild, user_id)

    row = [
        now_utc(),                 # timestamp
        str(message.author),       # Bot Name
        "BUY",                     # Action
        username,                  # User
        cash,                      # Cash
        bank,                      # Bank
        reason                     # Reason
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")
    print("スプレッドシートに書き込み:", row)

# =========================
# 起動
# =========================
client.run(TOKEN)
