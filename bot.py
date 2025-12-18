import os
import json
import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# 環境変数読み込み
TOKEN = os.environ["TOKEN"]
SERVICE_ACCOUNT_JSON = os.environ["SERVICE_ACCOUNT_JSON"]
SPREADSHEET_NAME = os.environ["SPREADSHEET_NAME"]
SHEET_NAME = os.environ["SHEET_NAME"]

# Google スプレッドシート接続
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(SERVICE_ACCOUNT_JSON), scope)
gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

CHANNEL_ID = 1389281116418211861  # Buyログが流れるチャンネル

# 既存ログの重複チェック用
processed_ids = set()

@client.event
async def on_ready():
    print(f'Bot は起動しました: {client.user}')

@client.event
async def on_message(message):
    # 対象チャンネル以外は無視
    if message.channel.id != CHANNEL_ID:
        return

    # 埋め込みがあるか確認
    if not message.embeds:
        return

    for embed in message.embeds:
        # Buy ログだけ処理
        if "buy item" in embed.description.lower():
            if message.id in processed_ids:
                return  # 既に処理済み
            processed_ids.add(message.id)

            # description から各項目を抽出
            desc = embed.description
            try:
                user_line = next(line for line in desc.splitlines() if line.startswith("User:"))
                amount_line = next(line for line in desc.splitlines() if line.startswith("Amount:"))
                reason_line = next(line for line in desc.splitlines() if line.startswith("Reason:"))
                date_line = next((line for line in desc.splitlines() if line.strip()), "")  # 日付は最後の行
            except StopIteration:
                continue

            user = user_line.replace("User:", "").strip()
            amount = amount_line.replace("Amount:", "").strip()
            reason = reason_line.replace("Reason:", "").strip()
            # 日本時間での記録
            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
            
            # スプレッドシートに追加
            sheet.append_row([now, user, amount, reason, date_line])

client.run(TOKEN)
