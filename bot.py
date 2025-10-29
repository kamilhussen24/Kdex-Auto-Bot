# bot.py
from telethon import TelegramClient, events, functions
from telethon.tl.types import ChatBannedRights
from datetime import datetime
import asyncio, pytz, os

# -------------------------------
# Environment Variables
# -------------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# -------------------------------
# Initialize Client
# -------------------------------
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
bd_tz = pytz.timezone("Asia/Dhaka")

# -------------------------------
# Admin Check: Owner + Admin
# -------------------------------
async def is_admin(event):
    if event.is_private:
        return True
    try:
        participant = await client.get_participant(event.chat_id, event.sender)
        return getattr(participant, 'creator', False) or getattr(participant, 'admin_rights', None) is not None
    except Exception as e:
        print(f"[ADMIN CHECK ERROR] {e}")
        return False

# -------------------------------
# Lock Group
# -------------------------------
async def lock_group(duration_hours=None):
    rights = ChatBannedRights(send_messages=True)
    try:
        await client(functions.messages.EditChatDefaultBannedRightsRequest(
            peer=GROUP_ID, banned_rights=rights
        ))
        if duration_hours:
            await client.send_message(GROUP_ID, f"গ্রুপটি {duration_hours} ঘন্টার জন্য লক করা হয়েছে।")
            await asyncio.sleep(duration_hours * 3600)
            await unlock_group(auto=True)
        else:
            await client.send_message(GROUP_ID, "গ্রুপ লক করা হয়েছে।")
    except Exception as e:
        print(f"[LOCK ERROR] {e}")

# -------------------------------
# Unlock Group
# -------------------------------
async def unlock_group(auto=False):
    rights = ChatBannedRights(send_messages=False)
    try:
        await client(functions.messages.EditChatDefaultBannedRightsRequest(
            peer=GROUP_ID, banned_rights=rights
        ))
        msg = "নির্ধারিত সময় শেষ। গ্রুপ আবার চালু।" if auto else "গ্রুপ আনলক করা হয়েছে।"
        await client.send_message(GROUP_ID, msg)
    except Exception as e:
        print(f"[UNLOCK ERROR] {e}")

# -------------------------------
# /lockfor
# -------------------------------
@client.on(events.NewMessage(pattern=r"(?i)^/lockfor(?:\s+(\d+)h?)?$", chats=GROUP_ID, outgoing=False))
async def lock_handler(event):
    if hasattr(event, "_handled"): return
    event._handled = True

    if not await is_admin(event):
        await event.reply("শুধুমাত্র মালিক/অ্যাডমিন এই কমান্ড ব্যবহার করতে পারবেন।")
        return

    duration_str = event.pattern_match.group(1)
    if duration_str:
        try:
            hours = int(duration_str)
            if hours <= 0: raise ValueError
            await lock_group(hours)
            await event.reply(f"গ্রুপ {hours} ঘন্টার জন্য লক।")
        except ValueError:
            await event.reply("ভুল ফরম্যাট। ব্যবহার: `/lockfor 5h` বা `/lockfor 5`")
    else:
        await lock_group()
        await event.reply("গ্রুপ লক করা হয়েছে।")

# -------------------------------
# /openchat
# -------------------------------
@client.on(events.NewMessage(pattern=r"(?i)^/openchat$", chats=GROUP_ID, outgoing=False))
async def unlock_handler(event):
    if hasattr(event, "_handled"): return
    event._handled = True

    if not await is_admin(event):
        await event.reply("শুধুমাত্র মালিক/অ্যাডমিন এই কমান্ড ব্যবহার করতে পারবেন।")
        return

    await unlock_group()
    await event.reply("গ্রুপ আনলক করা হয়েছে।")

# -------------------------------
# /start (No Duplicate)
# -------------------------------
@client.on(events.NewMessage(pattern=r"(?i)^/start(@\w+)?$", outgoing=False))
async def start_handler(event):
    if hasattr(event, "_handled"): return
    event._handled = True

    if event.is_private:
        message = (
            "হ্যালো! আমি **KDex Group** এর বট।\n\n"
            "আমার কাজ:\n"
            "• গ্রুপ স্বয়ংক্রিয়ভাবে লক/আনলক\n"
            "• শৃঙ্খলা বজায় রাখা"
        )
    else:
        message = "হ্যালো! আমি গ্রুপ লক/আনলক বট। `/lockfor 5h`, `/openchat`"
    await event.reply(message)

# -------------------------------
# Auto Night Lock (2:00 AM – 6:00 AM)
# -------------------------------
async def auto_night_lock():
    print("[AUTO LOCK] চালু হয়েছে...")
    while True:
        try:
            now = datetime.now(bd_tz)
            if now.hour == 2 and now.minute == 0:
                print("[AUTO] রাত ২টা – লক করা হচ্ছে...")
                await lock_group(4)
                await client.send_message(GROUP_ID, "রাত ২টা। গ্রুপ স্বয়ংক্রিয়ভাবে বন্ধ (সকাল ৬টা পর্যন্ত)।")
                await asyncio.sleep(3600)
            else:
                await asyncio.sleep(30)
        except Exception as e:
            print(f"[AUTO ERROR] {e}")
            await asyncio.sleep(60)

# -------------------------------
# Main
# -------------------------------
async def main():
    print("KDex Group Lock Bot চালু হয়েছে...")
    asyncio.create_task(auto_night_lock())
    await client.run_until_disconnected()

# -------------------------------
# Start
# -------------------------------
if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
