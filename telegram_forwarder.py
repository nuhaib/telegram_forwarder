import os
import asyncio
import logging
from telethon import TelegramClient, events, functions, types
from telethon.errors import ChatAdminRequiredError

# Configure logging (only logs errors to reduce RAM usage)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Load API credentials from environment variables
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

# Ensure credentials are set
if not api_id or not api_hash:
    raise ValueError("Missing API credentials. Set TELEGRAM_API_ID and TELEGRAM_API_HASH as environment variables.")

api_id = int(api_id)  # Convert API ID to integer

# Source & Target Channels (Script 1)
source_channel_script1 = [-1002496657106]  # Replace with actual source channel(s) for Script 1
target_channels_script1 = [-1002011167696, -1002358199357, -1002065146631, -1002099183759, -1002149387601, -1002200847921, -1002212730450, -1002197350918, -1002057497564, -1002469392993]  # Replace with actual target channels

# Initialize Telegram client
client = TelegramClient('script1_session', api_id, api_hash, flood_sleep_threshold=10)

@client.on(events.NewMessage(chats=source_channel_script1))
async def forward_messages(event):
    """Forward messages only to Script 1's assigned target channels."""
    msg = event.message
    text = msg.raw_text or ""
    media = msg.media if msg.media else None
    entities = msg.entities  # Preserve formatting
    buttons = msg.reply_markup  # Preserve buttons

    tasks = []
    for channel_id in target_channels_script1:
        tasks.append(send_message(channel_id, text, media, entities, buttons))

    await asyncio.gather(*tasks)

async def send_message(channel_id, text, media, entities, buttons):
    """Send messages while keeping formatting, media, and buttons intact."""
    try:
        await client.send_message(
            entity=channel_id,
            message=text,
            file=media if media else None,
            link_preview=True,
            buttons=buttons,
            formatting_entities=entities
        )
    except ChatAdminRequiredError:
        logger.error(f"Bot is not an admin in {channel_id}")
    except Exception as e:
        logger.error(f"Failed to send message to {channel_id}: {e}")

async def main():
    """Start the Telegram client."""
    print("Script 1 Forwarder is running...")
    await client.start()
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
