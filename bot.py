import os
import json
import discord
from discord.ext import commands
import gspread
from datetime import datetime
import pytz

# ----------------- 環境変数 -----------------
TOKEN = os.environ['TOKEN']  # Discord Bot Token
SERVICE_ACCOUNT_JSON = os.environ['SERVICE_ACCOUNT_JSON']  # JSON文字列
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
CHANNEL_ID = 1389281116418211861  # BuyログのチャンネルID

# ----------------- Google Sheets 接続 -----------------
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON))
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ここで重複防止用の最新行IDを保持
logged_messages = set()

# ----------------- Discord Bot セットアップ -----------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # メッセージ内容取得
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- ヘルパー関数 -----------------
def parse_buy_embed(embed: discord.Embed):
    """埋め込みからBuyログ情報を抽出"""
    if not embed or not embed.description:
        return None

    desc = embed.description
    lines = desc.split('\n')
    data = {"User": "", "Cash": "", "Bank": "", "Reason": ""}

    for line in lines:
        if line.startswith("**User:**"):
            data["User"] = line.replace("**User:**", "").strip()
        elif line.startswith("**Amount:**"):
            # CashとBankを分割
            parts = line.replace("**Amount:**", "").split("|")
            if len(parts) == 2:
                data["Cash"] = parts[0].replace("Cash:", "").strip(' `')
                data["Bank"] = parts[1].replace("Bank:", "").strip(' `')
        elif line.startswith("**Reason:**"):
            data["Reason"] = line.replace("**Reason:**", "").strip()

    return data

# ----------------- Discord イベント -----------------
@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # 対象チャンネルのみ
    if message.channel.id != CHANNEL_ID:
        return

    # 埋め込みがない場合は無視
    if not message.embeds:
        return

    for embed in message.embeds:
        data = parse_buy_embed(embed)
        if data:
            # DEBUG
            print(f"DEBUG EMBED TITLE: {embed.title}")
            print(f"DEBUG EMBED DESCRIPTION: {embed.description}")

            # 重複チェック
            if message.id in logged_messages:
                print("DEBUG: 重複メッセージ、スキップ")
                continue
            logged_messages.add(message.id)

            # 日本時間取得
            tz = pytz.timezone("Asia/Tokyo")
            timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            # スプレッドシート書き込み
            row = [timestamp, str(bot.user), "buy", data["User"], data["Cash"], data["Bank"], data["Reason"]]
            sheet.append_row(row)
            print(f"スプレッドシートに書き込み完了: {row}")

# ----------------- Bot 起動 -----------------
bot.run(TOKEN)
