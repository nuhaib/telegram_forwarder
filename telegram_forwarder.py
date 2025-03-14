import os
import re
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.errors import ChatAdminRequiredError

# Load API credentials securely from environment variables
api_id = int(os.getenv("TELEGRAM_API_ID", ""))
api_hash = os.getenv("TELEGRAM_API_HASH", "")

if not api_id or not api_hash:
    raise ValueError("Missing API credentials. Set TELEGRAM_API_ID and TELEGRAM_API_HASH as environment variables.")

# Source Channel ID (where messages are forwarded from)
source_channel_id = -1001880177414  # Replace with actual source channel

# Target Channels (where messages will be forwarded)
target_channels = [-1002389295588]  # List of target channels

# URL Replacement Settings
custom_url = "https://tc9987.cc/register?invite_code=0788812949052"
specific_channels = {-1002094341716, -10011223344}  # Channels where URLs should be removed

# Initialize Telegram client with flood protection
client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=60)

# Store admin channels globally to avoid fetching them repeatedly
admin_channels = set()
failed_channels = set()

async def get_admin_channels():
    """Fetch all channels where the user is an admin (runs once at startup)."""
    global admin_channels
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_channel:
            try:
                permissions = await client(functions.channels.GetParticipantRequest(dialog.id, 'me'))
                if isinstance(permissions.participant, types.ChannelParticipantAdmin):
                    admin_channels.add(dialog.id)
            except Exception:
                pass  # Ignore errors for inaccessible channels
    print(f"Admin channels fetched: {admin_channels}")

async def process_message(text, target_id):
    """Modifies message based on forwarding rules."""
    if not text:
        return text

    is_specific = target_id in specific_channels
    url_pattern = re.compile(r'https?://\S+')

    if is_specific:
        text = url_pattern.sub('', text)  # Remove URLs for specific channels
        blocked_texts = {'__', 'Game Link:', 'Game Link: https://tc9987.win/register?invite_code=9631811487671'}
        for phrase in blocked_texts:
            text = text.replace(phrase, '')  # Remove unwanted texts
    else:
        text = url_pattern.sub(custom_url, text)  # Replace URLs for general channels

    return text.strip()

async def send_message(channel_id, text, media, reply_markup, entities):
    """Send message asynchronously while preserving formatting, media, and buttons."""
    try:
        await client.send_message(
            entity=channel_id,
            message=text,
            file=media if media else None,
            link_preview=True,
            buttons=reply_markup,  # Preserve inline buttons
            formatting_entities=entities  # Preserve premium emojis and formatting
        )
    except ChatAdminRequiredError:
        failed_channels.add(channel_id)  # Avoid retrying failed channels
        print(f"Skipping {channel_id}, admin rights required.")
    except Exception as e:
        print(f"Failed to send message to {channel_id}: {e}")

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Forward messages while preserving media, formatting, emojis, and buttons."""
    global admin_channels

    msg = event.message
    text = msg.text or msg.caption or ''  # Extract text or caption
    media = msg.media if msg.media else None
    reply_markup = msg.reply_markup  # Keeps buttons (if any)
    entities = msg.entities  # Ensures formatting (bold, italic, premium emojis)

    tasks = []
    for channel_id in admin_channels:
        if channel_id in failed_channels:
            continue  # Skip failed channels
        processed_text = await process_message(text, channel_id)
        tasks.append(send_message(channel_id, processed_text, media, reply_markup, entities))

    await asyncio.gather(*tasks)  # Run all sends in parallel

async def main():
    """Startup function to initialize everything."""
    await client.start()  # Ensure the client is connected
    await get_admin_channels()  # Fetch admin channels once
    print("Forwarder is running...")
    await client.run_until_disconnected()

# Use asyncio.run() for proper event loop handling
if __name__ == "__main__":
    asyncio.run(main())
