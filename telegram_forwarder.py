import os
import asyncio
import logging
from telethon import TelegramClient, events

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API credentials from environment variables
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

# Ensure credentials are set
if not api_id or not api_hash:
    raise ValueError("Missing API credentials. Set TELEGRAM_API_ID and TELEGRAM_API_HASH as environment variables.")

api_id = int(api_id)  # Convert API ID to integer

# Channel IDs
source_channel_id = -1002496657106  # Replace with actual source channel
target_channels = [-1002144912406, -1002149387601, -1002200847921, -1002212730450, -1002020969286]  # Target channels

# Initialize Telegram client with optimized flood protection
client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=10)

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Handles new messages and forwards them efficiently."""
    for channel_id in target_channels:
        asyncio.create_task(forward_to_channel(channel_id, event))

async def forward_to_channel(channel_id, event):
    """Forwards a message to a target channel asynchronously."""
    try:
        # Use forward_messages for efficiency
        await client.forward_messages(channel_id, event.message)
        logger.info(f"Forwarded message to {channel_id}")
    except Exception as e:
        logger.error(f"Failed to forward message to {channel_id}: {e}")

async def main():
    """Starts the Telegram client and runs until disconnected."""
    try:
        await client.start()
        logger.info("Forwarder is running...")
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        await client.disconnect()

# Run the bot using an event loop (prevents nested loop errors)
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
