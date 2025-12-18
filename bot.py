import os
import json
import discord
from discord.ext import commands
import gspread
from datetime import datetime
import re
import pytz  # 日本時間に変換

# --- 環境変数 ---
TOKEN = os.environ['TOKEN']  # Discord Bot Token
SERVICE_ACCOUNT_JSON = os.environ['SERVICE_ACCOUNT_JSON']
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"
CHANNEL_ID = 1389281116418211861  # 監視するチャンネルID

# --- Discord Bot 設定 ---
intents = discord.Intents.default()
intents.message_content = True  # 埋め込みも読むため
bot = commands.Bot(command_prefix="!", intents=intents)

# --- スプレッドシート接続 ---
gc = gspread.service_account_from_dict(json.loads(SERVICE_ACCOUNT_JSON))
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# --- 重複チェック用 ---
processed_messages = set()

# --- 埋め込み解析関数 ---
def parse_buy_embed(embed):
    if embed.description is None:
        return None

    desc = embed.description
    print(f"DEBUG EMBED DESCRIPTION:\n{desc}")  # デバッグ出力

    # User
    user_match = re.search(r"\*\*User:\*\* <@(\d+)>", desc)
    user_id = user_match.group(1) if user_match else ""

    # Cash と Bank
    cash_bank_match = re.search(r"\*\*Amount:\*\* Cash: `(-?\d+)` \| Bank: `(-?\d+)`", desc)
    cash = cash_bank_match.group(1) if cash_bank_match else ""
    bank = cash_bank_match.group(2) if cash_bank_match else ""

    # Reason
    reason_match = re.search(r"\*\*Reason:\*\* (.+)", desc)
    reason = reason_match.group(1) if reason_match else ""

    return {
        "User": f"<@{user_id}>",
        "Cash": cash,
        "Bank": bank,
        "Reason": reason
    }

# --- メッセージ受信イベント ---
@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return

    if not message.embeds:
        return

    for embed in message.embeds:
        data = parse_buy_embed(embed)
        if not data:
            continue

        # 重複チェック
        msg_key = (message.id, data["Reason"])
        if msg_key in processed_messages:
            continue
        processed_messages.add(msg_key)

        # タイムスタンプ（日本時間）
        tz = pytz.timezone('Asia/Tokyo')
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        # スプレッドシートに書き込み
        row = [
            timestamp,
            str(bot.user),
            "buy",
            data.get("User", ""),
            data.get("Cash", ""),
            data.get("Bank", ""),
            data.get("Reason", "")
        ]
        sheet.append_row(row)
        print("スプレッドシートに書き込み完了:", row)  # デバッグ出力

# --- Bot 起動 ---
@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

bot.run(TOKEN)
