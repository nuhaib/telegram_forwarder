import re
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.errors import ChatAdminRequiredError

# Your Telegram credentials
api_id = 24316277  # Replace with your actual API ID
api_hash = '963c617eadb5c97c71aaee79df3a9e85'  # Replace with your actual API Hash

# URL Replacement Settings
custom_url = "https://tc9987.cc/register?invite_code=0788812949052"
specific_channels = {-1002094341716, -10011223344}  # Channels where URLs should be removed

# Source Channel ID
source_channel_id = -1001880177414  # Replace with actual source channel

client = TelegramClient('my_account', api_id, api_hash)

# Store admin channels globally to avoid fetching them repeatedly
admin_channels = set()

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

failed_channels = set()

@client.on(events.NewMessage(chats=source_channel_id))
async def forward_messages(event):
    """Forward messages while preserving emojis and formatting."""
    global admin_channels
    msg = event.message
    text = msg.text if msg.text else ''

    tasks = []  # Store async tasks to run them concurrently

    for channel_id in admin_channels:
        if channel_id in failed_channels:
            continue  # Skip failed channels

        processed_text = await process_message(text, channel_id)

        tasks.append(send_message(channel_id, processed_text, msg.media))

    await asyncio.gather(*tasks)  # Run all sends in parallel

async def send_message(channel_id, text, media):
    """Send message asynchronously."""
    try:
        await client.send_message(
            entity=channel_id,
            message=text,
            file=media if media else None,
            link_preview=False
        )
    except ChatAdminRequiredError:
        failed_channels.add(channel_id)  # Avoid retrying failed channels
    except Exception as e:
        print(f"Failed to send message to {channel_id}: {e}")

async def main():
    """Startup function to initialize everything."""
    await get_admin_channels()  # Fetch admin channels once
    print("Forwarder is running...")

with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
