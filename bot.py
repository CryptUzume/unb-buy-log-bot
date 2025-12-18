import os
import json
from datetime import datetime, timezone, timedelta
from discord.ext import commands
import gspread

# --- 環境変数の取得 ---
TOKEN = os.environ.get("TOKEN")
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")

if not TOKEN:
    raise ValueError("Discord トークンが環境変数 TOKEN に設定されていません。")

if not SERVICE_ACCOUNT_JSON:
    raise ValueError("サービスアカウント JSON が環境変数 SERVICE_ACCOUNT_JSON に設定されていません。")

# --- Google Sheets 認証 ---
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
gc = gspread.service_account_from_dict(creds_dict)

# --- スプレッドシート設定 ---
SPREADSHEET_NAME = "UnbilievableBoatLogs"
SHEET_NAME = "BuyLogs"
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# --- Discord Bot 設定 ---
intents = commands.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Buy ログをシートに追加する関数 ---
async def log_buy_to_sheet(user, item, amount):
    # 日本時間に変換
    jst = timezone(timedelta(hours=+9))
    now = datetime.now(jst).strftime("%Y/%m/%d %H:%M:%S")
    sheet.append_row([now, user, item, amount])

# --- Discord イベント ---
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.command()
async def buy(ctx, item: str, amount: float):
    """Buy コマンドでスプレッドシートに記録"""
    user = str(ctx.author)
    await log_buy_to_sheet(user, item, amount)
    await ctx.send(f"{user} の購入記録をスプレッドシートに追加しました。")

# --- Bot 起動 ---
bot.run(TOKEN)
