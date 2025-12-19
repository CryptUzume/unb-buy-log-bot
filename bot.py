import os
import discord
from discord.ext import tasks
import gspread
from google.oauth2.service_account import Credentials

# -------------------------------
# 環境変数 / 定数
# -------------------------------
TOKEN = os.getenv("TOKEN")
BUY_LOG_CHANNEL_ID = int(os.getenv("BUY_LOG_CHANNEL"))
SPREADSHEET_NAME = "Point shop"

# サービスアカウント情報は JSON 文字列で環境変数に
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

# -------------------------------
# Google Sheets 認証
# -------------------------------
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials_dict = None
import json
try:
    credentials_dict = json.loads(SERVICE_ACCOUNT_JSON)
except Exception as e:
    print("SERVICE_ACCOUNT_JSONの読み込みエラー:", e)
    exit(1)

credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
gc = gspread.authorize(credentials)

try:
    worksheet = gc.open(SPREADSHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    print(f"スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。")
    exit(1)

# -------------------------------
# Discord Client
# -------------------------------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 既に記録済みのメッセージIDを保持
existing_message_ids = set()
all_records = worksheet.get_all_records()
for record in all_records:
    # ヘッダーは除外されるので直接Message IDを使う場合はカラム追加が必要
    # 今回は "Reason" カラムに Message ID を入れる想定
    if "Reason" in record:
        existing_message_ids.add(record["Reason"])

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != BUY_LOG_CHANNEL_ID:
        return
    if message.author.bot:
        return

    # メッセージIDで重複チェック
    if str(message.id) in existing_message_ids:
        return

    # ユーザーID → ユーザー名
    username = str(message.author)

    # メッセージの内容を解析して必要な値を取得
    # ここはBot用にカスタマイズしてください
    action = "BUY"
    cash = 0
    bank = 0
    reason = str(message.id)  # 重複チェック用にMessage IDを保存

    # スプレッドシートに追加
    worksheet.append_row([
        str(message.created_at),
        client.user.name,
        action,
        username,
        cash,
        bank,
        reason
    ])

    # 登録済みに追加
    existing_message_ids.add(reason)

client.run(TOKEN)
