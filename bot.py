import os
import json
import asyncio
import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------
# 環境変数読み込み
# ----------------------------
TOKEN = os.getenv("TOKEN")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS")  # JSON文字列として環境変数にセット

print("DEBUG TOKEN:", repr(TOKEN))
if not TOKEN:
    raise ValueError("TOKEN が環境変数に設定されていません。")

if not GOOGLE_CREDENTIALS_JSON:
    raise ValueError("GOOGLE_CREDENTIALS が環境変数に設定されていません。")

# JSONを辞書に変換
try:
    google_credentials_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
except json.JSONDecodeError as e:
    raise ValueError("GOOGLE_CREDENTIALS が正しいJSONではありません。") from e

# ----------------------------
# Google Sheets 接続
# ----------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    google_credentials_dict, scope
)
gc = gspread.authorize(credentials)

# スプレッドシート名・シート名
SPREADSHEET_NAME = "YourSpreadsheetName"  # ここを変更
SHEET_NAME = "Sheet1"                     # ここを変更

try:
    sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    print(f"Connected to Google Sheet: {SPREADSHEET_NAME} -> {SHEET_NAME}")
except gspread.exceptions.APIError as e:
    print("Google Sheets API エラー:", e)
    raise e

# ----------------------------
# Discord Bot 初期化
# ----------------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# Botイベント例
# ----------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# ----------------------------
# 例: Google Sheets から値を取得して送信
# ----------------------------
@bot.command()
async def get_cell(ctx, row: int, col: int):
    try:
        value = sheet.cell(row, col).value
        await ctx.send(f"セル({row}, {col}) の値: {value}")
    except Exception as e:
        await ctx.send(f"エラー: {e}")

# ----------------------------
# Bot起動
# ----------------------------
bot.run(TOKEN)
