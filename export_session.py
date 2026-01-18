#!/usr/bin/env python3
"""
Export your Telegram session as a string for cloud deployment.
Run this AFTER you've authenticated with auth.py
"""

import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")


async def export_session():
    # Connect using existing file session
    client = TelegramClient("telegram_digest_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("Error: Not authenticated. Run 'python auth.py' first.")
        return

    # Export as string session
    string_session = StringSession.save(client.session)

    print("\n" + "=" * 60)
    print("Your session string (keep this SECRET!):")
    print("=" * 60)
    print(string_session)
    print("=" * 60)
    print("\nAdd this to your Render environment variables as:")
    print("TELEGRAM_SESSION_STRING=<the string above>")
    print()

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(export_session())
