# filename: purge_tools_telethon.py
import asyncio
from telethon import TelegramClient, events
from telethon.errors import MessageDeleteForbiddenError
from telethon.sessions import StringSession
from telethon.tl.types import MessageService

# ====== CONFIG: Yahin set karein ======
API_ID = 3947352            # my.telegram.org > API Development Tools [docs]
API_HASH = "d3865bffdb14c55f6585119086c5948d" # my.telegram.org se [docs]
TELETHON_STRING_SESSION = ""  # Optional: StringSession paste karein, warna blank chhodein [docs]
SESSION_NAME = "telethon_userbot"  # Agar string session blank ho to yeh .session file banega [docs]
BATCH_SIZE = 100  # deletion batch size [docs]
# =====================================

# Client init: StringSession prefer, else local .session file
if TELETHON_STRING_SESSION:
    client = TelegramClient(StringSession(TELETHON_STRING_SESSION), API_ID, API_HASH)
else:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def delete_in_batches(chat, ids):
    total = 0
    for i in range(0, len(ids), BATCH_SIZE):
        chunk = ids[i:i + BATCH_SIZE]
        try:
            await client.delete_messages(chat, chunk)  # high-level bulk delete
            total += len(chunk)
        except MessageDeleteForbiddenError:
            # Missing rights on some messages; skip
            pass
        await asyncio.sleep(0.4)
    return total

# ---------- 1) Only Deleted Account senders ----------
async def collect_deleted_only(chat):
    ids = []
    async for msg in client.iter_messages(chat):
        sender = getattr(msg, "sender", None)
        if sender and getattr(sender, "deleted", False):
            ids.append(msg.id)  # strictly only Deleted Account senders
    return ids

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.purge_deleted$"))
async def purge_deleted_handler(event):
    chat = await event.get_input_chat()
    note = await event.respond("Scanning only Deleted Account messages…")
    ids = await collect_deleted_only(chat)  # iterate history
    if not ids:
        return await note.edit("No messages from Deleted Accounts found.")
    count = await delete_in_batches(chat, ids)  # delete only those IDs
    await note.edit(f"Deleted {count} messages from Deleted Accounts only.")

# ---------- 2) Only join/leave service messages ----------
async def collect_join_service_only(chat):
    ids = []
    async for msg in client.iter_messages(chat):
        # Service messages are instances of MessageService (join/left/title/photo/created etc.)
        if isinstance(msg, MessageService):
            ids.append(msg.id)
    return ids

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.purge_joined$"))
async def purge_joined_handler(event):
    chat = await event.get_input_chat()
    note = await event.respond("Scanning join/leave service messages…")
    ids = await collect_join_service_only(chat)  # service-only
    if not ids:
        return await note.edit("No join/leave service messages found.")
    count = await delete_in_batches(chat, ids)  # delete service messages
    await note.edit(f"Deleted {count} join/leave service messages.")

if __name__ == "__main__":
    print("Starting Telethon userbot…")
    client.start()  # Interactive login if no StringSession
    client.run_until_disconnected()
    
