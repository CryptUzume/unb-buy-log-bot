import os
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

# ===== 設定 =====
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1389281116418211861
SPREADSHEET_NAME = "Point shop"
SHEET_NAME = "シート1"

# ===== Google Sheets 認証 =====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# ===== Bot 設定 =====
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Helper: 埋め込みから Buy ログを抽出 =====
def parse_buy_embed(embed: discord.Embed):
    # DEBUG: 埋め込み内容を全部表示
    print("DEBUG EMBED TITLE:", embed.title)
    print("DEBUG EMBED DESCRIPTION:", embed.description)
    for field in embed.fields:
        print("DEBUG FIELD:", field.name, field.value)

    # Buy ログかどうか判定
    if embed.description and "buy item" in embed.description:
        # description 例: "User: @鈿女\nAmount: Cash: -5 | Bank: 0\nReason: buy item (test-item1)\n今日 3:27"
        lines = embed.description.split("\n")
        data = {}
        for line in lines:
            if line.startswith("User:"):
                data["user"] = line.replace("User:", "").strip()
            elif line.startswith("Amount:"):
                data["amount"] = line.replace("Amount:", "").strip()
            elif line.startswith("Reason:"):
                data["reason"] = line.replace("Reason:", "").strip()
            elif line:
                data["time"] = line.strip()
        return data
    return None

# ===== Buy ログをスプレッドシートに書き込む =====
def write_to_sheet(data):
    if not data:
        return
    # 重複チェック: 最後の行と同じかどうか
    last_row = sheet.get_all_values()
    if last_row:
        last_entry = last_row[-1]
        if last_entry[0] == data.get("time") and last_entry[1] == data.get("user"):
            print("重複データのためスキップ:", data)
            return
    # 書き込む列順: 時刻 / ユーザー / 金額 / 理由
    row = [
        data.get("time", ""),
        data.get("user", ""),
        data.get("amount", ""),
        data.get("reason", "")
    ]
    sheet.append_row(row)
    print("スプレッドシートに書き込み完了:", row)

# ===== イベント =====
@bot.event
async def on_ready():
    print(f"Bot は起動しました: {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    if message.author.bot:
        # 埋め込みがある場合のみ処理
        for embed in message.embeds:
            data = parse_buy_embed(embed)
            if data:
                write_to_sheet(data)

# ===== Bot 起動 =====
bot.run(TOKEN)
