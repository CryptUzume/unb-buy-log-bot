import os
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone, timedelta

# ==== 設定 ====
CHANNEL_ID = 1389281116418211861  # Buyログが流れるチャンネル
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"

# ==== 環境変数から取得 ====
TOKEN = os.environ.get("TOKEN")
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")

if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("SERVICE_ACCOUNT_JSON が環境変数に設定されていません。")

# ==== gspread 初期化 ====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(SERVICE_ACCOUNT_JSON), scope
)
gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ==== Discord Bot 初期化 ====
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

    # 埋め込みが存在するか
    if not message.embeds:
        return

    embed = message.embeds[0]

    # "buy item" ログのみ
    if embed.title != "Balance updated":
        return

    data = {}
    for field in embed.fields:
        if field.name == "User":
            data["user"] = field.value.replace("@", "")
        elif field.name == "Amount":
            # Cash: -5 | Bank: 0 形式
            parts = field.value.split("|")
            cash = parts[0].split(":")[1].strip()
            bank = parts[1].split(":")[1].strip()
            data["cash"] = cash
            data["bank"] = bank
        elif field.name == "Reason":
            if not field.value.startswith("buy item"):
                return
            # buy item (アイテム名)
            item_name = field.value.split("(")[1].replace(")", "")
            data["item"] = item_name

    # タイムスタンプ（UTC→日本時間）
    timestamp_utc = message.created_at.replace(tzinfo=timezone.utc)
    timestamp_jst = timestamp_utc + timedelta(hours=9)
    data["time"] = timestamp_jst.strftime("%Y-%m-%d %H:%M:%S")

    # スプレッドシートに追加
    sheet.append_row([data["user"], data["cash"], data["bank"], data["item"], data["time"]])
    print(f"Logged: {data}")

bot.run(TOKEN)

