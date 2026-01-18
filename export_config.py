#!/usr/bin/env python3
"""
Export your config.yaml as a single-line string for cloud deployment.
"""

with open("config.yaml", "r") as f:
    content = f.read()

print("\n" + "=" * 60)
print("Your config (copy this entire block):")
print("=" * 60)
print(content)
print("=" * 60)
print("\nAdd this to your Render environment variables as:")
print("CONFIG_YAML")
print("(Paste the YAML content above as the value)")
print()
