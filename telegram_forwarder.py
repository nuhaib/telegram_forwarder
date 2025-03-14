import os
import asyncio
from telethon import TelegramClient, events

# Load API credentials from environment variables
api_id = int(os.getenv("TELEGRAM_API_ID", ""))
api_hash = os.getenv("TELEGRAM_API_HASH", "")

# Ensure credentials are set
if not api_id or not api_hash:
    raise ValueError("Missing API credentials. Set TELEGRAM_API_ID and TELEGRAM_API_HASH as environment variables.")

# Channel IDs
source_channel_id = -1002496657106  # Replace with actual source channel
target_channels = [-1002389295588]  # List of target channels

# Initialize Telegram client with flood protection
client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=60)

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Forwards all messages, preserving media, formatting, and buttons."""
    tasks = [
        client.send_message(
            channel_id,
            message=event.message.raw_text or "",
            file=event.message.media,
            link_preview=True,
            buttons=event.message.reply_markup,
            formatting_entities=event.message.entities
        )
        for channel_id in target_channels
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for channel_id, result in zip(target_channels, results):
        if isinstance(result, Exception):
            print(f"Failed to forward message to {channel_id}: {result}")

async def main():
    """Starts the Telegram client and runs until disconnected."""
    try:
        await client.start()
        print("Forwarder is running...")
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    finally:
        await client.disconnect()

# Run the bot using asyncio.run() to prevent nested loops
if __name__ == "__main__":
    asyncio.run(main())
