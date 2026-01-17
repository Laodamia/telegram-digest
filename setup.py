#!/usr/bin/env python3
"""
Telegram Digest - Interactive Setup
Run this script to configure the tool for first-time use.
"""

import os
import sys
import yaml
import asyncio
from pathlib import Path


def print_header(text):
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")


def print_step(num, text):
    print(f"\n📌 Step {num}: {text}")
    print("-" * 40)


def get_input(prompt, default=None):
    """Get input with optional default value."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def get_yes_no(prompt, default=True):
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    result = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not result:
        return default
    return result in ['y', 'yes']


def get_choice(prompt, options):
    """Get choice from list of options."""
    print(prompt)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        try:
            choice = int(input("Enter number: ").strip())
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        print("Invalid choice, try again.")


def main():
    print_header("Telegram Digest Setup")
    print("This wizard will help you configure Telegram Digest.")
    print("You'll need:")
    print("  • Telegram API credentials (from my.telegram.org)")
    print("  • Claude API key (from console.anthropic.com)")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    input()

    config = {
        "my_name": "",
        "show_dm_counts": True,
        "excluded_groups": [],
        "groups": []
    }
    env_vars = {}

    # -------------------------
    # Step 1: Telegram API
    # -------------------------
    print_step(1, "Telegram API Credentials")
    print("Go to https://my.telegram.org and create an application.")
    print("Select 'Desktop' or 'Other' as the platform.\n")

    env_vars["TELEGRAM_API_ID"] = get_input("Enter your api_id (number)")
    env_vars["TELEGRAM_API_HASH"] = get_input("Enter your api_hash (string)")

    # -------------------------
    # Step 2: Claude API
    # -------------------------
    print_step(2, "Claude API Key")
    print("Go to https://console.anthropic.com to get your API key.\n")

    env_vars["ANTHROPIC_API_KEY"] = get_input("Enter your Claude API key")

    # -------------------------
    # Step 3: Your Identity
    # -------------------------
    print_step(3, "Your Identity")
    print("This is used to detect messages directed at you.\n")

    name = get_input("Your first name", "Marta")
    handle = get_input("Your Telegram handle (without @)")

    config["my_name"] = name
    env_vars["MY_IDENTIFIERS"] = f"{name},{handle}" if handle else name

    # -------------------------
    # Step 4: DM Counts
    # -------------------------
    print_step(4, "Direct Messages")
    config["show_dm_counts"] = get_yes_no("Show unread counts for DMs?", True)

    # -------------------------
    # Step 5: Groups to Summarise
    # -------------------------
    print_step(5, "Groups to Summarise")
    print("Now let's configure which groups you want AI summaries for.")
    print("(You can always edit config.yaml later)\n")

    while True:
        add_group = get_yes_no("Add a group to summarise?", True)
        if not add_group:
            break

        group_name = get_input("Group name (exactly as it appears in Telegram)")

        group_config = {
            "name": group_name,
            "topics": []
        }

        print(f"\nConfiguring topics for '{group_name}'...")
        print("(Leave topic name empty when done adding topics)\n")

        while True:
            topic_name = get_input("Topic name (or Enter to finish)")
            if not topic_name:
                break

            topic_type = get_choice(
                f"Summary type for '{topic_name}':",
                ["technical", "logistics", "memes", "skip"]
            )

            threshold = 1
            if topic_type != "skip":
                threshold = int(get_input("Minimum messages to trigger summary", "5"))

            group_config["topics"].append({
                "name": topic_name,
                "type": topic_type,
                "threshold": threshold
            })

        # Default type for unlisted topics
        default_type = get_choice(
            f"Default type for OTHER topics in '{group_name}':",
            ["skip", "logistics", "technical"]
        )
        group_config["default_type"] = default_type

        config["groups"].append(group_config)
        print(f"\n✅ Added '{group_name}' with {len(group_config['topics'])} configured topics.\n")

    # -------------------------
    # Step 6: Excluded Groups
    # -------------------------
    print_step(6, "Excluded Groups")
    print("List groups you want to completely hide (no counts, no summaries).")
    print("(Leave empty when done)\n")

    while True:
        excluded = get_input("Group to exclude (or Enter to finish)")
        if not excluded:
            break
        config["excluded_groups"].append(excluded)

    # -------------------------
    # Write config files
    # -------------------------
    print_step(7, "Saving Configuration")

    # Write .env
    env_content = f"""# Telegram API credentials (from my.telegram.org)
TELEGRAM_API_ID={env_vars['TELEGRAM_API_ID']}
TELEGRAM_API_HASH={env_vars['TELEGRAM_API_HASH']}

# Claude API key (from console.anthropic.com)
ANTHROPIC_API_KEY={env_vars['ANTHROPIC_API_KEY']}

# Your identifiers for detecting personal action items (comma-separated)
MY_IDENTIFIERS={env_vars['MY_IDENTIFIERS']}

# Show DM counts in digest
SHOW_DM_COUNTS={'true' if config['show_dm_counts'] else 'false'}
"""

    with open(".env", "w") as f:
        f.write(env_content)
    print("✅ Created .env")

    # Write config.yaml
    yaml_config = {
        "my_name": config["my_name"],
        "excluded_groups": config["excluded_groups"],
        "groups": config["groups"]
    }

    yaml_content = f"""# Telegram Digest Configuration
# Generated by setup.py
# =============================

my_name: "{config['my_name']}"

# Show DM counts (true/false)
show_dm_counts: {str(config['show_dm_counts']).lower()}

# Groups to exclude from message counts entirely
excluded_groups:
"""
    for group in config["excluded_groups"]:
        yaml_content += f'  - "{group}"\n'

    if not config["excluded_groups"]:
        yaml_content += "  # - \"Example Group\"\n"

    yaml_content += """
# Groups with specific summarisation rules
groups:
"""
    for group in config["groups"]:
        yaml_content += f"""  - name: "{group['name']}"
    topics:
"""
        for topic in group["topics"]:
            yaml_content += f"""      - name: "{topic['name']}"
        type: "{topic['type']}"
        threshold: {topic['threshold']}
"""
        yaml_content += f"""    default_type: "{group.get('default_type', 'skip')}"

"""

    if not config["groups"]:
        yaml_content += """  # Example:
  # - name: "My Group"
  #   topics:
  #     - name: "General"
  #       type: "technical"
  #       threshold: 5
  #   default_type: "skip"
"""

    yaml_content += """
# Summary type definitions:
# - technical: Arguments, pros/cons, top 1-2 links/papers, context from previous convos
# - memes: Top 3 memes, explain AI safety context if relevant
# - logistics: To-dos, calls for help, anything directed at you
# - skip: No summary for this topic
"""

    with open("config.yaml", "w") as f:
        f.write(yaml_content)
    print("✅ Created config.yaml")

    # -------------------------
    # Telegram Authentication
    # -------------------------
    print_step(8, "Telegram Authentication")
    print("Now we need to authenticate with Telegram.")
    print("You'll receive a code on your phone.\n")

    do_auth = get_yes_no("Authenticate now?", True)

    if do_auth:
        # Import and run auth
        try:
            from telegram_client import TelegramDigestClient

            async def run_auth():
                client = TelegramDigestClient()
                await client.connect()
                print("\n✅ Authentication successful!")
                summary = await client.get_unread_summary()
                total = len(summary["dms"]) + len(summary["groups"]) + len(summary["supergroups"])
                print(f"Found {total} chats with unread messages.")
                await client.disconnect()

            asyncio.run(run_auth())
        except Exception as e:
            print(f"\n❌ Authentication failed: {e}")
            print("You can try again later with: python auth.py")
    else:
        print("Run 'python auth.py' later to authenticate.")

    # -------------------------
    # Done!
    # -------------------------
    print_header("Setup Complete!")
    print("To start the digest server:")
    print("  python main.py")
    print()
    print("Then open http://localhost:8000 in your browser.")
    print()
    print("To edit your configuration later:")
    print("  • .env - API keys and identifiers")
    print("  • config.yaml - Groups and summary rules")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
