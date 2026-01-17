"""
Summariser module using Claude API.
Different prompts for different topic types.
"""

import os
from typing import List, Dict
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Support multiple identifiers (name, handle, etc.)
_identifiers = os.getenv("MY_IDENTIFIERS", "Marta")
MY_IDENTIFIERS = [x.strip() for x in _identifiers.split(",")]
MY_NAME = MY_IDENTIFIERS[0]  # Use first one as display name


def format_messages_for_prompt(messages: List[Dict]) -> str:
    """Format messages into a readable format for the prompt."""
    formatted = []
    for msg in messages:
        sender = msg.get("sender", "Unknown")
        text = msg.get("text", "")
        date = msg.get("date", "")[:16]  # Truncate to datetime without seconds

        if text:
            # Note if message is a reply
            reply_note = ""
            if msg.get("reply_to_id"):
                reply_note = " [replying to earlier message]"

            formatted.append(f"[{date}] {sender}{reply_note}: {text}")
        elif msg.get("has_media"):
            formatted.append(f"[{date}] {sender}: [media/image]")

    return "\n".join(formatted)


async def summarise_technical(messages: List[Dict], topic_name: str) -> str:
    """
    Summarise technical AI discussion.
    Extracts: topic, arguments pro/con, top 1-2 papers/links, notes if relates to previous convo.
    """
    if not messages:
        return "No messages to summarise."

    messages_text = format_messages_for_prompt(messages)

    prompt = f"""Summarise this Telegram discussion from the "{topic_name}" topic.

MESSAGES:
{messages_text}

Extract and format as follows:

## Main Topic(s)
[What was being discussed - 1-2 sentences]

## Key Arguments
**Pro/supporting points:**
- [bullet points]

**Con/opposing points:**
- [bullet points]

## Links & Papers
[List top 1-2 most interesting/relevant links or papers mentioned. If many were shared, prioritise the most discussed ones. If none, write "None mentioned."]

## Context Notes
[If the conversation references previous discussions or assumes context from earlier, note this briefly. If standalone, write "Self-contained discussion."]

Be concise but preserve technical nuance. Use bullet points."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def summarise_memes(messages: List[Dict], topic_name: str) -> str:
    """
    Summarise meme channel.
    Extracts: top 3 memes, explains AI safety context if relevant.
    """
    if not messages:
        return "No memes to report."

    messages_text = format_messages_for_prompt(messages)

    prompt = f"""Summarise the memes shared in this Telegram channel "{topic_name}".

MESSAGES:
{messages_text}

Format as follows:

## Top 3 Memes
For each meme, provide:
1. **[Brief description]** - [Why it's funny/relevant]
   - AI Safety Context: [If this relates to recent AI safety news/events, explain. If not, write "General humour"]

2. ...

3. ...

If fewer than 3 memes were shared, just describe what was shared.
If messages describe images you can't see, do your best to infer from context and reactions."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def summarise_logistics(messages: List[Dict], topic_name: str) -> str:
    """
    Summarise logistics/coordination discussion.
    Extracts: to-dos, calls for help, anything directed at specific user.
    """
    if not messages:
        return "No messages to summarise."

    messages_text = format_messages_for_prompt(messages)

    prompt = f"""Summarise this Telegram coordination/logistics discussion from "{topic_name}".

MESSAGES:
{messages_text}

Extract and format as follows:

## To-Dos & Action Items
[List any tasks or action items mentioned, noting who they're assigned to if specified]
- [ ] [Task] — assigned to: [person or "unassigned"]

## Calls for Help
[Any requests for volunteers, assistance, or input]

## Specifically for {MY_NAME}
[Anything directly addressed to or mentioning any of: {', '.join(MY_IDENTIFIERS)}. If nothing, write "Nothing specific."]

## Quick Summary
[1-2 sentence overview of what was discussed]

Be concise. Focus on actionable items."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def summarise_invites(messages: List[Dict], topic_name: str) -> str:
    """
    Summarise event invites.
    Extracts: what, when, where, who is inviting. Ignores discussion.
    """
    if not messages:
        return "No invites to report."

    messages_text = format_messages_for_prompt(messages)

    prompt = f"""Extract event invites from this Telegram channel "{topic_name}".

MESSAGES:
{messages_text}

For each INVITE (ignore replies/discussion), provide a one-liner:
**[Event name]** — [Date/time] @ [Location] — invited by [Person]

If any detail is missing, write "TBD" for that field.
Only list actual invites, not discussion about them.
If no invites found, write "No new invites."

Keep it concise - one line per invite."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def summarise(
    messages: List[Dict],
    topic_name: str,
    summary_type: str
) -> str:
    """
    Main summarisation function - routes to appropriate summariser.

    Args:
        messages: List of message dicts
        topic_name: Name of the topic/channel
        summary_type: One of "technical", "memes", "logistics", "invites", "skip"
    """
    if summary_type == "skip":
        return None

    if summary_type == "technical":
        return await summarise_technical(messages, topic_name)
    elif summary_type == "memes":
        return await summarise_memes(messages, topic_name)
    elif summary_type == "logistics":
        return await summarise_logistics(messages, topic_name)
    elif summary_type == "invites":
        return await summarise_invites(messages, topic_name)
    else:
        # Default to logistics for unknown types
        return await summarise_logistics(messages, topic_name)


# For testing
if __name__ == "__main__":
    import asyncio

    test_messages = [
        {"sender": "Alice", "text": "Has anyone read the new Anthropic paper on constitutional AI?", "date": "2024-01-15T10:00"},
        {"sender": "Bob", "text": "Yes! I think the approach is promising but I'm skeptical about scalability", "date": "2024-01-15T10:05", "reply_to_id": 1},
        {"sender": "Carol", "text": "Link: https://arxiv.org/abs/example - I agree with Bob, the compute requirements are concerning", "date": "2024-01-15T10:10"},
        {"sender": "Alice", "text": "Fair point. Though they did show it works with smaller models too", "date": "2024-01-15T10:15"},
    ]

    async def test():
        result = await summarise_technical(test_messages, "AI Discussion")
        print(result)

    asyncio.run(test())
