import re
import asyncio
import json
import os
from telethon import TelegramClient, events, functions, types
from telethon.errors import ChatAdminRequiredError

# Your Telegram credentials
api_id = 26454923  # Replace with your actual API ID
api_hash = 'd20b1753029d86716271b18f783b43ed'  # Replace with your actual API Hash
source_channel_id = -1002496657106  # Replace with actual source channel

client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=60)  # Let Telethon handle rate limits

admin_channels = set()
failed_channels = set()
CACHE_FILE = "admin_channels.json"  # Cache file to avoid multiple API requests

async def get_admin_channels():
    """Fetch and store the list of admin channels while handling rate limits."""
    global admin_channels
    if os.path.exists(CACHE_FILE):  # Load cached admin channels
        with open(CACHE_FILE, "r") as f:
            admin_channels = set(json.load(f))
        print(f"Loaded cached admin channels: {admin_channels}")
        return

    try:
        dialogs = await client.get_dialogs(limit=50)  # Limit API calls to prevent rate limits
        new_admin_channels = set()
        for dialog in dialogs:
            if dialog.is_channel:
                try:
                    permissions = await client(functions.channels.GetParticipantRequest(dialog.id, 'me'))
                    if isinstance(permissions.participant, types.ChannelParticipantAdmin):
                        new_admin_channels.add(dialog.id)
                except Exception as e:
                    if 'A wait of' in str(e):
                        wait_time = int(''.join(filter(str.isdigit, str(e))))  # Extract wait time
                        print(f"Rate limit hit! Retrying after {wait_time} seconds...")
                        await asyncio.sleep(wait_time + 1)  # Wait slightly longer and retry
                        return await get_admin_channels()
                    print(f"Skipping {dialog.id}: {e}")

        admin_channels = new_admin_channels

        # Cache admin channels
        with open(CACHE_FILE, "w") as f:
            json.dump(list(admin_channels), f)

        print(f"Admin channels updated: {admin_channels}")
    except Exception as e:
        print(f"Error updating admin channels: {e}")

def process_message(text):
    """Removes URLs from the message instantly."""
    return re.sub(r'https?://\S+', '', text) if text else text

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Instantly forward messages with parallel execution."""
    msg = event.message
    processed_text = process_message(msg.text or '')

    tasks = []
    for channel_id in admin_channels:
        if channel_id in failed_channels:
            continue  # Skip channels that failed before

        tasks.append(
            client.send_message(
                entity=channel_id,
                message=processed_text,
                file=msg.media if msg.media else None,
                link_preview=False
            )
        )

    # Execute all sends in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle failed deliveries
    for channel_id, result in zip(admin_channels, results):
        if isinstance(result, Exception):
            print(f"Failed to send message to {channel_id}: {result}")
            if isinstance(result, ChatAdminRequiredError):
                failed_channels.add(channel_id)  # Mark for skipping in future

async def main():
    await client.start()
    await get_admin_channels()  # Run admin check once at startup
    print("Forwarder is running...")
    await client.run_until_disconnected()

asyncio.run(main())
