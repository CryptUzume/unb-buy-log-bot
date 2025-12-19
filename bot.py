import os
import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 環境変数
TOKEN = os.getenv("TOKEN")  # Discord Bot Token
SPREADSHEET_NAME = "Point shop"
BUY_LOG_CHANNEL = int(os.getenv("BUY_LOG_CHANNEL"))

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")  # JSON文字列を直接環境変数に入れる
gc = gspread.service_account_from_dict(eval(creds_json))
worksheet = gc.open(SPREADSHEET_NAME).sheet1  # 既存シートを使用

# Helper: ユーザーID → ユーザー名変換
async def get_username(user_id):
    user = await client.fetch_user(user_id)
    return str(user)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    check_buy_log.start()

# 購入ログ確認（簡易例）
@tasks.loop(seconds=60)
async def check_buy_log():
    channel = client.get_channel(BUY_LOG_CHANNEL)
    if not channel:
        print("Buy log channel not found.")
        return

    async for message in channel.history(limit=50):
        # すでにスプレッドシートにあるかは確認しない（同じユーザーでも全件記録）
        try:
            user_name = await get_username(message.author.id)
            row = [
                str(message.created_at),
                client.user.name,
                "BUY",
                user_name,
                "",  # Cash
                "",  # Bank
                message.content  # Reason
            ]
            worksheet.append_row(row)
        except Exception as e:
            print(f"Error writing row: {e}")

client.run(TOKEN)
