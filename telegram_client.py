"""
Telegram client wrapper using Telethon.
Handles authentication and message fetching.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from telethon import TelegramClient
from telethon.tl.types import Channel, User, Chat, Message
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "telegram_digest_session"


class TelegramDigestClient:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    async def connect(self):
        """Connect to Telegram. Will prompt for phone/code on first run."""
        await self.client.start()
        print("Connected to Telegram")

    async def disconnect(self):
        """Disconnect from Telegram."""
        await self.client.disconnect()

    async def get_all_dialogs(self):
        """Get all dialogs (chats, groups, channels) with unread counts."""
        dialogs = await self.client.get_dialogs()
        return dialogs

    async def get_unread_summary(self):
        """
        Get summary of all unread messages.
        Returns dict with counts for DMs and groups.
        """
        dialogs = await self.get_all_dialogs()

        summary = {
            "dms": [],      # 1-1 conversations
            "groups": [],   # Groups without topics
            "supergroups": []  # Groups that might have topics (forums)
        }

        for dialog in dialogs:
            if dialog.unread_count == 0:
                continue

            # Skip archived chats
            if dialog.archived:
                continue

            entity = dialog.entity
            name = dialog.name or "Unknown"

            item = {
                "id": entity.id,
                "name": name,
                "unread_count": dialog.unread_count,
            }

            if isinstance(entity, User):
                summary["dms"].append(item)
            elif isinstance(entity, Channel):
                if getattr(entity, 'forum', False):
                    # This is a forum (has topics)
                    item["is_forum"] = True
                    summary["supergroups"].append(item)
                else:
                    summary["groups"].append(item)
            elif isinstance(entity, Chat):
                summary["groups"].append(item)

        return summary

    async def get_group_topics(self, group_id: int, count_recent_messages: bool = False):
        """Get all topics in a forum/supergroup with message counts.

        Args:
            group_id: The forum group ID
            count_recent_messages: If True, actually count messages (slower but more accurate)
        """
        try:
            entity = await self.client.get_entity(group_id)
            if not getattr(entity, 'forum', False):
                return []

            # Get forum topics
            from telethon.tl.functions.channels import GetForumTopicsRequest
            result = await self.client(GetForumTopicsRequest(
                channel=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100
            ))

            topics = []
            for topic in result.topics:
                unread = getattr(topic, 'unread_count', 0)

                # Optionally count actual recent messages (slower)
                if count_recent_messages:
                    try:
                        messages = await self.get_topic_messages(
                            group_id, topic.id, limit=50, since_hours=24
                        )
                        unread = len(messages)
                    except:
                        pass

                topics.append({
                    "id": topic.id,
                    "title": topic.title,
                    "unread_count": unread
                })

            return topics
        except Exception as e:
            print(f"Error getting topics for group {group_id}: {e}")
            return []

    async def get_topic_messages(
        self,
        group_id: int,
        topic_id: int,
        limit: int = 100,
        since_hours: int = 24
    ):
        """
        Get messages from a specific topic in a forum.

        Args:
            group_id: The group/channel ID
            topic_id: The topic/thread ID
            limit: Max messages to fetch
            since_hours: Only fetch messages from last N hours
        """
        try:
            entity = await self.client.get_entity(group_id)

            # Calculate the cutoff time
            since = datetime.now() - timedelta(hours=since_hours)

            messages = []
            async for message in self.client.iter_messages(
                entity,
                limit=limit,
                reply_to=topic_id,  # This filters to a specific topic
                offset_date=None
            ):
                if message.date.replace(tzinfo=None) < since:
                    break

                msg_data = {
                    "id": message.id,
                    "date": message.date.isoformat(),
                    "sender": await self._get_sender_name(message),
                    "text": message.text or "",
                    "has_media": message.media is not None,
                }

                # Check if it's a reply to another message
                if message.reply_to:
                    msg_data["reply_to_id"] = message.reply_to.reply_to_msg_id

                messages.append(msg_data)

            return messages
        except Exception as e:
            print(f"Error getting messages for topic {topic_id}: {e}")
            return []

    async def get_chat_messages(
        self,
        chat_id: int,
        limit: int = 100,
        since_hours: int = 24
    ):
        """
        Get messages from a regular chat (DM or non-forum group).
        """
        try:
            entity = await self.client.get_entity(chat_id)
            since = datetime.now() - timedelta(hours=since_hours)

            messages = []
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.date.replace(tzinfo=None) < since:
                    break

                messages.append({
                    "id": message.id,
                    "date": message.date.isoformat(),
                    "sender": await self._get_sender_name(message),
                    "text": message.text or "",
                    "has_media": message.media is not None,
                })

            return messages
        except Exception as e:
            print(f"Error getting messages for chat {chat_id}: {e}")
            return []

    async def _get_sender_name(self, message: Message) -> str:
        """Get the sender's name from a message."""
        try:
            if message.sender:
                if isinstance(message.sender, User):
                    return message.sender.first_name or message.sender.username or "Unknown"
                elif hasattr(message.sender, 'title'):
                    return message.sender.title
            return "Unknown"
        except:
            return "Unknown"


# For testing/first-time auth
async def main():
    client = TelegramDigestClient()
    await client.connect()

    print("\n📬 Fetching unread summary...")
    summary = await client.get_unread_summary()

    print("\n=== DMs ===")
    for dm in summary["dms"]:
        print(f"  {dm['name']}: {dm['unread_count']} messages")

    print("\n=== Groups ===")
    for group in summary["groups"]:
        print(f"  {group['name']}: {group['unread_count']} messages")

    print("\n=== Forums (with topics) ===")
    for sg in summary["supergroups"]:
        print(f"  {sg['name']}: {sg['unread_count']} messages")
        topics = await client.get_group_topics(sg["id"])
        for topic in topics:
            if topic["unread_count"] > 0:
                print(f"    └─ {topic['title']}: {topic['unread_count']} unread")

    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
