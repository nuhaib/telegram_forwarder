import asyncio
from telethon import TelegramClient, events

# Your Telegram credentials
api_id = 24316277  # Replace with your actual API ID
api_hash = '963c617eadb5c97c71aaee79df3a9e85'  # Replace with your actual API Hash
source_channel_id = -1002496657106  # Replace with actual source channel

# Initialize the Telegram client with flood protection
client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=60)

# Define the target channels where messages should be forwarded
target_channels = [-1002389295588]

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Forwards all messages, including premium stickers, emojis, media, and formatting."""
    msg = event.message
    
    # Extract message text and media
    message_text = msg.raw_text if msg.raw_text else None
    media = msg.media if msg.media else None
    reply_markup = msg.reply_markup  # Keeps buttons (if any)
    entities = msg.entities  # Preserves formatting (bold, italic, premium emojis)

    # Forward the message to all target channels
    tasks = []
    for channel_id in target_channels:
        try:
            tasks.append(
                client.send_message(
                    entity=channel_id,
                    message=message_text,  # Use cleaned-up message text
                    file=media,  # Keeps media
                    link_preview=True,  # Enables URL previews
                    buttons=reply_markup,  # Keeps inline buttons
                    formatting_entities=entities,  # Ensures premium emojis are forwarded correctly
                )
            )
        except Exception as e:
            print(f"Failed to forward message to {channel_id}: {e}")

    # Send all messages asynchronously
    await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    await client.start()
    print("Forwarder is running...")
    await client.run_until_disconnected()

# Run the bot
if __name__ == "__main__":  
    client.loop.run_until_complete(main())
