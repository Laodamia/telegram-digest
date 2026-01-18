# Telegram Digest

A web app that shows your unread Telegram messages with AI-powered summaries for specific groups.

## Features

- **Message counts** for all DMs and groups
- **AI summaries** for configured groups/topics using Claude
- **Four summary types:**
  - `technical` - Arguments, pros/cons, key links/papers
  - `logistics` - To-dos, action items, mentions of you
  - `memes` - Top memes/jokes with context when needed
  - `invites` - One-liner per event invite
- **Exclude groups** you don't want to see
- **Accessible from anywhere** when deployed

## Quick Start

### Option 1: Interactive Setup (Recommended)

```bash
pip install -r requirements.txt
python setup.py
```

Follow the prompts to configure everything.

### Option 2: Manual Setup

1. **Get API credentials:**
   - Telegram: https://my.telegram.org → Create app → Get `api_id` and `api_hash`
   - Claude: https://console.anthropic.com → Get API key

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Then edit .env with your API keys
   ```

3. **Create `config.yaml`:**
   ```bash
   cp config.example.yaml config.yaml
   # Then edit config.yaml with your groups and preferences
   ```

4. **Authenticate with Telegram:**
   ```bash
   python auth.py
   ```

5. **Run the app:**
   ```bash
   python main.py
   ```

6. **Open** http://localhost:8000

### Optional: Install command

To run `telegram-digest` from anywhere in your terminal:

```bash
./install.sh
```

Then just type `telegram-digest` from any directory.

## Configuration

### config.yaml

```yaml
my_name: "YourName"

# Hide these groups completely
excluded_groups:
  - "Noisy Group"
  - "Archived Stuff"

# Groups to summarise
groups:
  - name: "AI Discussion"
    topics:
      - name: "General"
        type: "technical"
        threshold: 10  # Only summarise if 10+ messages
      - name: "Memes"
        type: "memes"
        threshold: 1
    default_type: "skip"  # Skip unlisted topics
```

### Summary Types

| Type | What it extracts |
|------|------------------|
| `technical` | Topic, arguments pro/con, links/papers, context |
| `logistics` | To-dos, action items, mentions of you |
| `memes` | Top 3 memes/jokes with context when needed |
| `invites` | One-liner per invite: what, when, where, who |
| `skip` | No summary |

## Deployment (Render)

1. **Export your session string** (locally, after running `auth.py`):
   ```bash
   python export_session.py
   ```
   Copy the session string.

2. **Push code to GitHub**

3. **Create new Web Service on Render:**
   - Connect your GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Set environment variables in Render:**
   - `TELEGRAM_API_ID` - your Telegram API ID
   - `TELEGRAM_API_HASH` - your Telegram API hash
   - `ANTHROPIC_API_KEY` - your Claude API key
   - `MY_IDENTIFIERS` - your name and Telegram handle (comma-separated)
   - `TELEGRAM_SESSION_STRING` - from step 1
   - `DIGEST_SECRET_TOKEN` - pick a random secret string
   - `CONFIG_YAML` - paste your config.yaml contents (run `python export_config.py`)

5. **Deploy and access at:**
   ```
   https://your-app.onrender.com?token=YOUR_SECRET_TOKEN
   ```

## Files

```
telegram-digest/
├── setup.py              # Interactive setup wizard
├── auth.py               # First-time Telegram auth
├── main.py               # FastAPI backend
├── telegram_client.py    # Telethon wrapper
├── summariser.py         # Claude API summaries
├── config.yaml           # Your configuration
├── .env                  # API keys (keep private!)
├── static/
│   └── index.html        # Web frontend
└── *.session             # Telegram session (keep private!)
```

## Troubleshooting

**"proxies" error:** Run `pip install --upgrade anthropic httpx`

**Archived chats showing:** They're filtered by default now

**Need to re-authenticate:** Delete `*.session` file and run `python auth.py`
