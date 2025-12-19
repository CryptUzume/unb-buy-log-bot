import os
import json
import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ===== 環境変数 =====
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")

BUY_LOG_CHANNEL = os.getenv("BUY_LOG_CHANNEL")
if not BUY_LOG_CHANNEL:
    raise ValueError("BUY_LOG_CHANNEL が環境変数に設定されていません。")
BUY_LOG_CHANNEL = int(BUY_LOG_CHANNEL)

SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# ===== スプレッドシート接続 =====
service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_NAME = "DiscordBuyLog"
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # 既存シートを使用

# ===== Discord クライアント =====
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot は起動しました: {client.user}")

@client.event
async def on_message(message):
    if message.channel.id != BUY_LOG_CHANNEL:
        return

    # Embed がない場合は無視
    if not message.embeds:
        return

    embed = message.embeds[0]

    # Buy ログだけ処理
    if not embed.title or "buy" not in embed.title.lower():
        return

    # ===== デバッグ出力 =====
    print("DEBUG EMBED TITLE:", embed.title)
    print("DEBUG EMBED DESCRIPTION:", embed.description)

    # Embed 説明を解析
    lines = embed.description.split("\n")
    user_line = next((l for l in lines if l.startswith("**User:**")), "")
    cash_line = next((l for l in lines if l.startswith("**Amount:**")), "")
    reason_line = next((l for l in lines if l.startswith("**Reason:**")), "")

    # ユーザー名取得
    user_id = user_line.split("<@")[-1].split(">")[0] if "<@" in user_line else ""
    user_obj = message.guild.get_member(int(user_id)) if user_id else None
    username = user_obj.name if user_obj else user_id

    # 金額取得
    cash = ""
    bank = ""
    if cash_line:
        parts = cash_line.split("|")
        cash = parts[0].split("`")[1] if len(parts) > 0 else ""
        bank = parts[1].split("`")[1] if len(parts) > 1 else ""

    # 理由取得
    reason = reason_line.split("**Reason:**")[-1].strip() if reason_line else ""

    # タイムスタンプ
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # スプレッドシートに書き込み（ヘッダーは既存のため書かない）
    row = [timestamp, str(client.user), "BUY", username, cash, bank, reason]
    worksheet.append_row(row)

    print("スプレッドシートに書き込み完了:", row)

client.run(TOKEN)
