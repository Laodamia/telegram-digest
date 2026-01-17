"""
First-time Telegram authentication script.
Run this once locally to create the session file.
"""

import asyncio
from telegram_client import TelegramDigestClient


async def main():
    print("=" * 50)
    print("Telegram Digest - First Time Authentication")
    print("=" * 50)
    print()
    print("This will connect to your Telegram account.")
    print("You'll be prompted for your phone number and a code.")
    print()

    client = TelegramDigestClient()
    await client.connect()

    print()
    print("✅ Authentication successful!")
    print(f"Session file created: telegram_digest_session.session")
    print()
    print("You can now run the main app with: python main.py")

    # Quick test
    print()
    print("Running quick test...")
    summary = await client.get_unread_summary()

    total_dms = len(summary["dms"])
    total_groups = len(summary["groups"])
    total_forums = len(summary["supergroups"])

    print(f"Found: {total_dms} DMs, {total_groups} groups, {total_forums} forums with topics")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
