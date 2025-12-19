import os
import json
import discord
import gspread
from datetime import datetime

# 環境変数
TOKEN = os.getenv("DISCORD_TOKEN")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
SHEET_NAME = os.getenv("SHEET_NAME")
TARGET_CHANNEL_ID = int(os.getenv("BUY_LOG_CHANNEL"))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True  # メンバー情報取得

client = discord.Client(intents=intents)

# gspread 初期化
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON))
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# シートヘッダー
try:
    sheet.append_row(["timestamp", "Bot Name", "Action", "User", "Cash", "Bank", "Reason"])
except Exception:
    pass

def parse_buy_embed(embed: discord.Embed):
    """BUY ログの埋め込みを解析"""
    user_id = ""
    cash = ""
    bank = ""
    reason = ""
    
    if embed.description:
        lines = embed.description.split("\n")
        for line in lines:
            if line.startswith("**User:**"):
                user_id = line.split("<@")[-1].split(">")[0].strip()
            elif line.startswith("**Amount:**"):
                amount = line.replace("**Amount:**", "").strip()
                if "Cash:" in amount and "Bank:" in amount:
                    parts = amount.split("|")
                    cash = parts[0].replace("Cash:", "").strip(" `")
                    bank = parts[1].replace("Bank:", "").strip(" `")
            elif line.startswith("**Reason:**"):
                reason = line.replace("**Reason:**", "").strip()
    return user_id, cash, bank, reason

async def resolve_user_name(guild: discord.Guild, user_id: str):
    """ユーザーIDをユーザー名に変換"""
    try:
        member = await guild.fetch_member(int(user_id))
        return str(member)
    except Exception:
        return user_id  # 取得できない場合はIDのまま

@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    if not message.embeds:
        return

    for embed in message.embeds:
        user_id, cash, bank, reason = parse_buy_embed(embed)
        if not reason:
            continue

        # ユーザーID → ユーザー名
        user_name = await resolve_user_name(message.guild, user_id)

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        bot_name = client.user.name
        action = "buy"

        row = [timestamp, bot_name, action, user_name, cash, bank, reason]

        try:
            sheet.append_row(row)
            print("スプレッドシートに書き込み完了:", row)
        except Exception as e:
            print("スプレッドシート書き込みエラー:", e)

client.run(TOKEN)
