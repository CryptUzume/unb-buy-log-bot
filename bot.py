import discord
import gspread
import json
import os
from discord.ext import commands

# ==========================
# 設定
# ==========================
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")  # 環境変数にBotトークン
SPREADSHEET_NAME = "BuyLog"                 # スプレッドシート名
SHEET_NAME = "Sheet1"                        # シート名

# サービスアカウントのJSONを環境変数にセットしておく場合
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")

if SERVICE_ACCOUNT_JSON is None:
    raise ValueError("SERVICE_ACCOUNT_JSON が設定されていません")

creds_dict = json.loads(SERVICE_ACCOUNT_JSON)

# ==========================
# gspread認証
# ==========================
gc = gspread.service_account_from_dict(creds_dict)

try:
    sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
except gspread.SpreadsheetNotFound:
    raise ValueError(f"{SPREADSHEET_NAME} というスプレッドシートが見つかりません。共有設定を確認してください。")

# ==========================
# Discord Bot設定
# ==========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# Buyログ検知
# ==========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Botメッセージは無視

    # ここでBuyログを検知する条件を指定
    if "Buy" in message.content:
        user = message.author.name
        content = message.content
        row = [user, content]

        try:
            sheet.append_row(row)
            print(f"スプレッドシートに書き込み: {row}")
        except Exception as e:
            print(f"スプレッドシート書き込みエラー: {e}")

    await bot.process_commands(message)

# ==========================
# 起動
# ==========================
bot.run(TOKEN)
