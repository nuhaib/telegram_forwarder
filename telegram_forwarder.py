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

# Source & Target Channels
source_channel_id = -1002496657106  # Replace with actual source channel
target_channels = [-1002144912406, -1002149387601, -1002200847921, -1002212730450, -1002020969286]  # Target channels

# Initialize Telegram client with optimized flood protection
client = TelegramClient('my_account', api_id, api_hash, flood_sleep_threshold=10)

# Store admin channels to avoid redundant API calls
admin_channels = set()
failed_channels = set()  # Track channels where sending fails

async def get_admin_channels():
    """Fetches all channels where the bot is an admin to prevent unnecessary API calls."""
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

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Handles new messages and sends them efficiently without 'Forwarded from' tag."""
    global admin_channels

    msg = event.message
    text = msg.text if msg.text else ""

    tasks = []  # Store tasks to run them concurrently
    for channel_id in admin_channels:
        if channel_id in failed_channels:
            continue  # Skip channels that failed previously

        tasks.append(send_message(channel_id, text, msg.media))

    await asyncio.gather(*tasks)  # Run all sends in parallel

async def send_message(channel_id, text, media):
    """Sends message asynchronously to prevent delays."""
    try:
        await client.send_message(
            entity=channel_id,
            message=text,
            file=media if media else None,
            link_preview=False  # Disables link previews to speed up sending
        )
    except ChatAdminRequiredError:
        failed_channels.add(channel_id)  # Avoid retrying failed channels
    except Exception as e:
        logger.error(f"Failed to send message to {channel_id}: {e}")

async def main():
    """Startup function to initialize everything."""
    await get_admin_channels()  # Fetch admin channels once at startup
    print("Forwarder is running...")

# Run the bot using an event loop
with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
