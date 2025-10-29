from telethon import TelegramClient, events, functions
from telethon.tl.types import ChannelParticipantsAdmins, ChatBannedRights
from datetime import datetime, timedelta
import asyncio, pytz, os

API_ID = int(os.getenv("API_ID", 1234567))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
GROUP_ID = int(os.getenv("GROUP_ID", -100xxxxxxxxxx))

client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
bd_tz = pytz.timezone("Asia/Dhaka")

# Admin check
async def is_admin(event):
    try:
        admins = await client.get_participants(event.chat_id, filter=ChannelParticipantsAdmins)
        return any(admin.id == event.sender_id for admin in admins)
    except:
        return False

# Lock & Unlock
async def lock_group(duration_hours=None):
    rights = ChatBannedRights(send_messages=True)
    try:
        await client(functions.messages.EditChatDefaultBannedRights(peer=GROUP_ID, banned_rights=rights))
        if duration_hours:
            await client.send_message(GROUP_ID, f"🔒 গ্রুপটি {duration_hours} ঘন্টার জন্য বন্ধ রাখা হয়েছে। অনুগ্রহ করে অপেক্ষা করুন 💬")
            await asyncio.sleep(duration_hours * 3600)
            await unlock_group(auto=True)
        else:
            await client.send_message(GROUP_ID, "🔒 গ্রুপটি এখন বন্ধ রয়েছে।")
    except Exception as e:
        print("Lock error:", e)

async def unlock_group(auto=False):
    rights = ChatBannedRights(send_messages=False)
    try:
        await client(functions.messages.EditChatDefaultBannedRights(peer=GROUP_ID, banned_rights=rights))
        msg = "✅ নির্ধারিত সময় শেষ — গ্রুপটি আবার চালু করা হয়েছে 💫" if auto else "✅ গ্রুপটি আনলক করা হয়েছে, সবাই কথা বলতে পারেন 😄"
        await client.send_message(GROUP_ID, msg)
    except Exception as e:
        print("Unlock error:", e)

# /lock command
@client.on(events.NewMessage(pattern=r"^/lock(?: (\d+)h)?$"))
async def lock_handler(event):
    if not await is_admin(event):
        await event.reply("⚠️ শুধুমাত্র অ্যাডমিন এই কমান্ড ব্যবহার করতে পারবেন।")
        return
    duration = event.pattern_match.group(1)
    if duration:
        await lock_group(int(duration))
    else:
        await lock_group()

# /unlock command
@client.on(events.NewMessage(pattern=r"^/unlock$"))
async def unlock_handler(event):
    if not await is_admin(event):
        await event.reply("⚠️ শুধুমাত্র অ্যাডমিন এই কমান্ড ব্যবহার করতে পারবেন।")
        return
    await unlock_group()

# Auto night lock (2AM–6AM)
async def auto_night_lock():
    while True:
        now = datetime.now(bd_tz)
        if now.hour == 2 and now.minute == 0:
            await lock_group()
            await client.send_message(GROUP_ID, "🌙 রাত ২টা — গ্রুপটি স্বয়ংক্রিয়ভাবে বন্ধ হয়েছে (সকাল ৬টা পর্যন্ত)।")
            await asyncio.sleep(4 * 3600)
            await unlock_group(auto=True)
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(auto_night_lock())
    await client.run_until_disconnected()

print("🚀 Smart Telegram Group Lock Bot started...")
client.loop.run_until_complete(main())
