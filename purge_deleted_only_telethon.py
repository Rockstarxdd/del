# filename: purge_deleted_only_telethon.py
import asyncio
from telethon import TelegramClient, events
from telethon.errors import MessageDeleteForbiddenError
from telethon.sessions import StringSession

# ====== CONFIG: Yahin set karein ======
API_ID = 123456            # my.telegram.org > API Development Tools [1]
API_HASH = "your_api_hash" # my.telegram.org se [1]
TELETHON_STRING_SESSION = ""  # Optional: StringSession paste karein, warna blank chhodein [3]
SESSION_NAME = "telethon_userbot"  # Agar string session blank ho to yeh .session file banega [1]
BATCH_SIZE = 100  # deletion batch size [1]
# =====================================

# Client init: StringSession prefer, else local .session file
if TELETHON_STRING_SESSION:
    client = TelegramClient(StringSession(TELETHON_STRING_SESSION), API_ID, API_HASH)
else:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def collect_deleted_only(chat):
    ids = []
    async for msg in client.iter_messages(chat):
        sender = getattr(msg, "sender", None)
        if sender and getattr(sender, "deleted", False):
            ids.append(msg.id)  # strictly only Deleted Account senders [1]
    return ids

async def delete_in_batches(chat, ids):
    total = 0
    for i in range(0, len(ids), BATCH_SIZE):
        chunk = ids[i:i + BATCH_SIZE]
        try:
            await client.delete_messages(chat, chunk)  # high-level bulk delete [1][2]
            total += len(chunk)
        except MessageDeleteForbiddenError:
            # Missing rights on some messages; skip [2]
            pass
        await asyncio.sleep(0.4)
    return total

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.purge_deleted$"))
async def handler(event):
    chat = await event.get_input_chat()
    note = await event.respond("Scanning only Deleted Account messages…")
    ids = await collect_deleted_only(chat)  # iterate history [1]
    if not ids:
        return await note.edit("No messages from Deleted Accounts found.")
    count = await delete_in_batches(chat, ids)  # delete only those IDs [1][2]
    await note.edit(f"Deleted {count} messages from Deleted Accounts only.")

if __name__ == "__main__":
    print("Starting Telethon userbot…")
    client.start()  # Interactive login if no StringSession [1]
    client.run_until_disconnected()
  
