import re
import asyncio
import json
import os
from telethon import TelegramClient, events, functions, types
from telethon.errors import ChatAdminRequiredError, FloodWaitError

# Your Telegram credentials
api_id = 26454923  # Replace with your actual API ID
api_hash = 'd20b1753029d86716271b18f783b43ed'  # Replace with your actual API Hash
source_channel_id = -1002496657106  # Replace with actual source channel

client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=60)  # Prevents rate limits

admin_channels = set()
failed_channels = set()
CACHE_FILE = "admin_channels.json"  # Cache file to avoid repeated API calls

async def get_admin_channels():
    """Fetch the list of admin channels while handling rate limits."""
    global admin_channels
    if os.path.exists(CACHE_FILE):  # Load cached data if available
        with open(CACHE_FILE, "r") as f:
            admin_channels = set(json.load(f))
        print(f"Loaded cached admin channels: {admin_channels}")
        return

    try:
        dialogs = await client.get_dialogs(limit=50)  # Reduce API requests for premium accounts
        new_admin_channels = set()
        for dialog in dialogs:
            if dialog.is_channel:
                try:
                    permissions = await client(functions.channels.GetParticipantRequest(dialog.id, 'me'))
                    if isinstance(permissions.participant, types.ChannelParticipantAdmin):
                        new_admin_channels.add(dialog.id)
                except FloodWaitError as e:
                    print(f"Skipping {dialog.id} due to rate limit: {e}")
                    continue
                except Exception as e:
                    print(f"Skipping {dialog.id}: {e}")

        admin_channels = new_admin_channels

        # Save admin channels to cache
        with open(CACHE_FILE, "w") as f:
            json.dump(list(admin_channels), f)

        print(f"Admin channels updated: {admin_channels}")
    except Exception as e:
        print(f"Error updating admin channels: {e}")

def process_message(text):
    """Removes URLs from the message instantly while preserving formatting."""
    return re.sub(r'https?://\S+', '', text) if text else text

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Forwards all messages, including premium stickers, emojis, media, and formatting."""
    msg = event.message

    # Process text (remove URLs but keep emojis & formatting)
    processed_text = process_message(msg.text or msg.message)

    # Extract media & formatting
    media = msg.media if msg.media else None  # Supports images, videos, stickers
    reply_markup = msg.reply_markup  # Keeps buttons (if any)
    entities = msg.entities  # Ensures formatting (bold, italics, premium emojis) is preserved

    tasks = []
    for channel_id in admin_channels:
        if channel_id in failed_channels:
            continue  # Skip failed channels

        try:
            tasks.append(
                client.send_message(
                    entity=channel_id,
                    message=processed_text,
                    file=media,  # Ensures media (stickers, emojis, images) is forwarded
                    link_preview=False,
                    formatting_entities=entities,  # Correctly forwards emojis & formatting
                    buttons=reply_markup  # Keeps inline buttons
                )
            )
        except Exception as e:
            print(f"Failed to forward message to {channel_id}: {e}")

    # Send all messages asynchronously
    await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    await client.start()
    await get_admin_channels()  # Fetch admin channels at startup
    print("Forwarder is running...")
    await client.run_until_disconnected()

asyncio.run(main())
