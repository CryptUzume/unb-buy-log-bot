import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- 環境変数から読み込む ---
TOKEN = os.environ.get("DISCORD_TOKEN")  # Discord Bot トークン
BUY_LOG_CHANNEL = int(os.environ.get("BUY_LOG_CHANNEL", 0))  # Buyログ用チャンネルID
SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME")  # スプシ名
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")  # タブ名
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")  # JSON文字列

# --- Googleスプレッドシート認証 ---
import json
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# --- Discord クライアント ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.channel.id == BUY_LOG_CHANNEL and not message.author.bot:
        # Buyログをスプレッドシートに追記
        sheet.append_row([message.author.name, message.content])
        print(f"Logged to spreadsheet: {message.author.name}, {message.content}")

client.run(TOKEN)
