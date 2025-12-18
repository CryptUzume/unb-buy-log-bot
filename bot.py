@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    # 埋め込みの description が空の場合は fields を結合
    if embed.description:
        content = embed.description
    elif embed.fields:
        content = "\n".join(f"{f.name}: {f.value}" for f in embed.fields)
    else:
        return

    if "Reason: buy item" not in content:
        return

    unique_id = f"{message.id}"
    if unique_id in logged_messages:
        return
    logged_messages.add(unique_id)

    lines = content.split("\n")
    user_line = next((l for l in lines if l.startswith("User:")), "")
    amount_line = next((l for l in lines if l.startswith("Amount:")), "")
    reason_line = next((l for l in lines if l.startswith("Reason:")), "")
    time_line = lines[-1] if lines else ""

    now_jst = datetime.now(timezone(timedelta(hours=9)))
    timestamp = now_jst.strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        user_line.replace("User: ", ""),
        amount_line.replace("Amount: ", ""),
        reason_line.replace("Reason: ", ""),
        time_line
    ]

    sheet.append_row(row)
    print(f"記録しました: {row}")
