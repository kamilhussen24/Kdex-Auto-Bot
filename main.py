from telethon import TelegramClient, events
from telethon.tl.types import ChatBannedRights
from datetime import datetime
import asyncio, pytz, os

# -------------------------------
# Environment Variables
# -------------------------------
API_ID = int(os.getenv("API_ID", 1234567))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
GROUP_ID = int(os.getenv("GROUP_ID", "-1003083776944"))

# -------------------------------
# Initialize Client
# -------------------------------
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
bd_tz = pytz.timezone("Asia/Dhaka")

# -------------------------------
# Admin Check (Fixed)
# -------------------------------
async def is_admin(event):
    try:
        participant = await client.get_participant(event.chat_id, event.sender)
        return getattr(participant, 'admin_rights', None) is not None
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
            await client.send_message(
                GROUP_ID,
                f"গ্রুপটি {duration_hours} ঘন্টার জন্য বন্ধ রাখা হয়েছে। অনুগ্রহ করে অপেক্ষা করুন"
            )
            await asyncio.sleep(duration_hours * 3600)
            await unlock_group(auto=True)
        else:
            await client.send_message(GROUP_ID, "গ্রুপটি এখন বন্ধ রয়েছে।")
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
        msg = (
            "নির্ধারিত সময় শেষ। গ্রুপটি আবার চালু করা হয়েছে"
            if auto
            else "গ্রুপটি আনলক করা হয়েছে, এখন সবাই কথা বলতে পারেন"
        )
        await client.send_message(GROUP_ID, msg)
    except Exception as e:
        print(f"[UNLOCK ERROR] {e}")

# -------------------------------
# /lockfor Command (case-insensitive)
# -------------------------------
@client.on(events.NewMessage(pattern=r"(?i)^/lockfor(?:\s+(\d+)h?)?$", chats=GROUP_ID))
async def lock_handler(event):
    if not await is_admin(event):
        await event.reply("শুধুমাত্র অ্যাডমিন এই কমান্ড ব্যবহার করতে পারবেন।")
        return

    duration_str = event.pattern_match.group(1)
    if duration_str:
        try:
            hours = int(duration_str)
            if hours <= 0:
                raise ValueError
            await lock_group(hours)
            await event.reply(f"গ্রুপ {hours} ঘন্টার জন্য লক করা হয়েছে।")
        except ValueError:
            await event.reply("সঠিক ফরম্যাট: `/lockfor 5h` অথবা `/lockfor 5`")
    else:
        await lock_group()
        await event.reply("গ্রুপ লক করা হয়েছে।")

# -------------------------------
# /openchat Command
# -------------------------------
@client.on(events.NewMessage(pattern=r"(?i)^/openchat$", chats=GROUP_ID))
async def unlock_handler(event):
    if not await is_admin(event):
        await event.reply("শুধুমাত্র অ্যাডমিন এই কমান্ড ব্যবহার করতে পারবেন।")
        return
    await unlock_group()
    await event.reply("গ্রুপ আনলক করা হয়েছে।")

# -------------------------------
# /start Command (Private + Group, No Duplicate)
# -------------------------------
@client.on(events.NewMessage(pattern=r"(?i)^/start(@\w+)?$"))
async def start_handler(event):
    # Prevent duplicate handling
    if hasattr(event, "_handled_start"):
        return
    event._handled_start = True

    if event.is_private:
        message = (
            "হ্যালো! আমি **KDex Group** এর দায়িত্বশীল বট।\n"
            "দয়া করে আমাকে বিরক্ত করবেন না, আমি অনেক ব্যস্ত থাকি সবসময়।😌\n\n"
            "আমার কাজ: স্বয়ংক্রিয়ভাবে গ্রুপ লক/আনলক করা এবং শৃঙ্খলা বজায় রাখা।"
        )
    else:
        message = (
            "হ্যালো! আমি **KDex Group** এর দায়িত্বশীল বট।\n"
            "দয়া করে আমাকে বিরক্ত করবেন না, আমি অনেক ব্যস্ত থাকি সবসময়।😌\n\n"
            "আমার কাজ: স্বয়ংক্রিয়ভাবে গ্রুপ লক/আনলক করা।"
        )
    await event.reply(message)

# -------------------------------
# Auto Night Lock (2:00 AM – 6:00 AM Dhaka Time)
# -------------------------------
async def auto_night_lock():
    print("[AUTO LOCK] স্বয়ংক্রিয় লক সিস্টেম চালু হয়েছে...")
    while True:
        try:
            now = datetime.now(bd_tz)
            current_time = now.strftime("%H:%M")
            
            # 2:00 AM - Lock
            if current_time == "02:00":
                print(f"[AUTO] {current_time} - গ্রুপ লক করা হচ্ছে...")
                await lock_group(4)  # 4 hours
                await client.send_message(
                    GROUP_ID,
                    "এখন রাত ২টা। গ্রুপ স্বয়ংক্রিয়ভাবে বন্ধ হয়েছে (সকাল ৬টা পর্যন্ত)।"
                )
                await asyncio.sleep(3600)  # Wait 1 hour before next check
                continue

            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"[AUTO LOCK ERROR] {e}")
            await asyncio.sleep(60)

# -------------------------------
# Main Function
# -------------------------------
async def main():
    print("Smart Telegram Group Lock Bot চালু হয়েছে...")
    # Start auto lock in background
    asyncio.create_task(auto_night_lock())
    await client.run_until_disconnected()

# -------------------------------
# Start Bot
# -------------------------------
with client:
    client.loop.run_until_complete(main())
