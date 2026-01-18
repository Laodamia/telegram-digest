#!/bin/bash
# Install telegram-digest command for easy access from anywhere

INSTALL_DIR=$(pwd)

# Detect OS and set target
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    TARGET="/usr/local/bin/telegram-digest"

    echo "Installing telegram-digest command..."

    # Create the launcher script
    sudo tee "$TARGET" > /dev/null << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python main.py
EOF

    sudo chmod +x "$TARGET"

    echo "Done! You can now run 'telegram-digest' from anywhere."
else
    echo "Unsupported OS. Please manually create an alias:"
    echo "  alias telegram-digest='cd \"$INSTALL_DIR\" && python main.py'"
fi
