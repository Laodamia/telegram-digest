"""
Telegram Digest - FastAPI Backend
Provides API for fetching and summarising Telegram messages.
"""

import os
import yaml
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from telegram_client import TelegramDigestClient
from summariser import summarise

# Load config
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

# Global telegram client
tg_client: Optional[TelegramDigestClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage telegram client lifecycle."""
    global tg_client
    tg_client = TelegramDigestClient()
    await tg_client.connect()
    print("✅ Telegram client connected")
    yield
    await tg_client.disconnect()
    print("👋 Telegram client disconnected")


app = FastAPI(title="Telegram Digest", lifespan=lifespan)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class DigestResponse(BaseModel):
    """Response model for digest endpoint."""
    message_counts: dict
    summaries: list
    errors: list


def get_topic_config(group_name: str, topic_name: str) -> dict:
    """Get config for a specific topic, or default if not found."""
    for group in CONFIG.get("groups", []):
        if group["name"].lower() == group_name.lower():
            # Check specific topics
            for topic in group.get("topics", []):
                if topic["name"].lower() == topic_name.lower():
                    return topic

            # Return default type if exists
            if "default_type" in group:
                return {
                    "name": topic_name,
                    "type": group["default_type"],
                    "threshold": 1
                }

    return None


def is_configured_group(group_name: str) -> bool:
    """Check if a group is in our config."""
    for group in CONFIG.get("groups", []):
        if group["name"].lower() == group_name.lower():
            return True
    return False


def get_group_config(group_name: str) -> dict:
    """Get config for a standalone group (not a forum with topics)."""
    for group in CONFIG.get("groups", []):
        if group["name"].lower() == group_name.lower():
            # Only return if it has a direct type (not topics)
            if "type" in group:
                return group
    return None


def is_excluded_group(group_name: str) -> bool:
    """Check if a group should be excluded from counts."""
    excluded = CONFIG.get("excluded_groups", [])
    return group_name.lower() in [g.lower() for g in excluded]


@app.get("/")
async def root():
    """Serve the main page."""
    return FileResponse("static/index.html")


@app.get("/api/digest")
async def get_digest(since_hours: int = 24):
    """
    Get full digest:
    1. Message counts for all chats
    2. AI summaries for configured topics
    """
    if not tg_client:
        raise HTTPException(status_code=500, detail="Telegram client not connected")

    errors = []
    summaries = []

    # Get unread summary (counts for everything)
    unread = await tg_client.get_unread_summary()

    # Check if DM counts should be shown
    show_dms = CONFIG.get("show_dm_counts", True)

    message_counts = {
        "dms": [{"name": d["name"], "count": d["unread_count"]} for d in unread["dms"]] if show_dms else [],
        "groups": [{"name": g["name"], "count": g["unread_count"]} for g in unread["groups"] if not is_excluded_group(g["name"])],
        "forums": []
    }

    # Process forums (groups with topics)
    for forum in unread["supergroups"]:
        forum_name = forum["name"]

        # Skip excluded groups
        if is_excluded_group(forum_name):
            continue

        forum_id = forum["id"]

        forum_data = {
            "name": forum_name,
            "total_count": forum["unread_count"],
            "topics": []
        }

        # Get topics for this forum
        topics = await tg_client.get_group_topics(forum_id)

        for topic in topics:
            topic_name = topic["title"]
            topic_id = topic["id"]
            unread_count = topic.get("unread_count", 0)

            topic_data = {
                "name": topic_name,
                "count": unread_count
            }
            forum_data["topics"].append(topic_data)

            # Check if we should summarise this topic
            if not is_configured_group(forum_name):
                continue

            topic_config = get_topic_config(forum_name, topic_name)
            if not topic_config:
                continue

            summary_type = topic_config.get("type", "skip")
            threshold = topic_config.get("threshold", 1)

            if summary_type == "skip":
                continue

            if unread_count < threshold:
                continue

            # Fetch messages and summarise
            try:
                messages = await tg_client.get_topic_messages(
                    forum_id,
                    topic_id,
                    limit=100,
                    since_hours=since_hours
                )

                if messages:
                    summary_text = await summarise(messages, topic_name, summary_type)
                    if summary_text:
                        summaries.append({
                            "group": forum_name,
                            "topic": topic_name,
                            "type": summary_type,
                            "message_count": len(messages),
                            "summary": summary_text
                        })
            except Exception as e:
                errors.append(f"Error summarising {forum_name}/{topic_name}: {str(e)}")

        message_counts["forums"].append(forum_data)

    # Process standalone groups (non-forums) for summaries
    for group in unread["groups"]:
        group_name = group["name"]
        group_id = group["id"]
        unread_count = group["unread_count"]

        # Skip excluded groups
        if is_excluded_group(group_name):
            continue

        # Check if this group has a direct summary config
        group_config = get_group_config(group_name)
        if not group_config:
            continue

        summary_type = group_config.get("type", "skip")
        threshold = group_config.get("threshold", 1)

        if summary_type == "skip":
            continue

        if unread_count < threshold:
            continue

        # Fetch messages and summarise
        try:
            messages = await tg_client.get_chat_messages(
                group_id,
                limit=100,
                since_hours=since_hours
            )

            if messages:
                summary_text = await summarise(messages, group_name, summary_type)
                if summary_text:
                    summaries.append({
                        "group": group_name,
                        "topic": "(all)",
                        "type": summary_type,
                        "message_count": len(messages),
                        "summary": summary_text
                    })
        except Exception as e:
            errors.append(f"Error summarising {group_name}: {str(e)}")

    return DigestResponse(
        message_counts=message_counts,
        summaries=summaries,
        errors=errors
    )


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "telegram_connected": tg_client is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
