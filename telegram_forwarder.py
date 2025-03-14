import asyncio
import logging
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Telegram API Credentials
API_ID = 26454923  # Replace with your actual API ID
API_HASH = "d20b1753029d86716271b18f783b43ed"  # Replace with your actual API Hash
SESSION_NAME = "my_account"  # Session file name

# Source and Target Channels
SOURCE_CHAT_ID = -1002496657106  # Replace with actual source channel
TARGET_CHAT_IDS = [-1002389295588]  # List of target chat IDs

# Initialize Telegram Client with flood protection
client = TelegramClient(SESSION_NAME, API_ID, API_HASH, flood_sleep_threshold=60)

@client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def forward_messages(event):
    """Forwards all messages, including stickers, premium emojis, media, and formatting."""
    msg = event.message

    # Extract message details
    message_text = msg.raw_text or None  # Keep original text
    media = msg.media if msg.media else None  # Keep all media (stickers, images, videos, etc.)
    reply_markup = msg.reply_markup  # Keeps inline buttons
    entities = msg.entities  # Preserves formatting (bold, italic, premium emojis)

    tasks = []
    for channel_id in TARGET_CHAT_IDS:
        try:
            task = client.send_message(
                entity=channel_id,
                message=message_text,
                file=media,  # Forwards images, videos, stickers, etc.
                link_preview=True,  # Enables URL previews
                buttons=reply_markup,  # Keeps inline buttons
                formatting_entities=entities,  # Ensures premium emojis and formatting
            )
            tasks.append(task)
            logging.info(f"Forwarding message to {channel_id}")

        except FloodWaitError as e:
            logging.warning(f"Rate limit exceeded! Sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)

        except RPCError as e:
            logging.error(f"RPC error while sending to {channel_id}: {e}")

        except Exception as e:
            logging.error(f"Unexpected error while forwarding to {channel_id}: {e}")

    await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    """Starts the Telegram client and handles disconnects gracefully."""
    while True:
        try:
            await client.start()
            logging.info("Forwarder bot is running...")
            await client.run_until_disconnected()
        except Exception as e:
            logging.error(f"Client disconnected unexpectedly: {e}")
            logging.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)  # Prevents tight reconnect loops

if __name__ == "__main__":
    client.loop.run_until_complete(main())
