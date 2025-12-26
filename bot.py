import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone, timedelta
import re

# ========= 設定 =========

DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"

TARGET_CHANNEL_ID = 1454126930189095126  # BUYログが流れるチャンネルID
SPREADSHEET_NAME = "BUY_LOG"
SHEET_NAME = "Sheet1"

# ========= Google Sheets =========

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

print("✅ Google Sheets 接続成功")

# ========= Discord =========

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

JST = timezone(timedelta(hours=9))

# ========= ユーティリティ =========

def extract_reason(embed: discord.Embed) -> str:
    """
    embed 内のどこかから Reason を拾う
    """
    # fields から探す
    for field in embed.fields:
        if "Reason" in field.name:
            return field.value.strip()

    # description から探す
    if embed.description:
        m = re.search(r"\*\*Reason:\*\*\s*(.+)", embed.description)
        if m:
            return m.group(1).strip()

    return "UNKNOWN"

def extract_amount(text: str) -> tuple[str, str]:
    """
    Cash / Bank を拾う（無ければ 0）
    """
    cash = "0"
    bank = "0"

    m_cash = re.search(r"Cash:\s*`?(-?\d+)`?", text)
    m_bank = re.search(r"Bank:\s*`?(-?\d+)`?", text)

    if m_cash:
        cash = m_cash.group(1)
    if m_bank:
        bank = m_bank.group(1)

    return cash, bank

# ========= イベント =========

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    print(f"📩 message received: {message.id}")

    # embed 前提
    if not message.embeds:
        print("⏭ embed なし → 無視")
        return

    embed = message.embeds[0]

    raw_text = (
        (embed.title or "") + "\n" +
        (embed.description or "")
    )

    for f in embed.fields:
        raw_text += f"\n{f.name}: {f.value}"

    # ========= BUY 判定（これだけ） =========
    if "buy item" not in raw_text.lower():
        print("⏭ BUY 判定できず")
        return

    print("✅ BUY 判定 OK")

    # ========= 抽出 =========

    user_id = "UNKNOWN"
    m_user = re.search(r"<@(\d+)>", raw_text)
    if m_user:
        user_id = m_user.group(1)

    cash, bank = extract_amount(raw_text)
    reason = extract_reason(embed)

    timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    # ========= Sheets 書き込み =========

    row = [
        timestamp,
        user_id,
        cash,
        bank,
        reason
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")

    print("📝 Sheets に書き込み完了")

# ========= 起動 =========

bot.run(DISCORD_TOKEN)
