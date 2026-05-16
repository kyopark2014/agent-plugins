#!/bin/bash

# Update script: git pull, rebuild and run Docker
echo "Update Script"
echo "=================================="

# Step 1: Git pull
echo ""
echo "Pulling latest changes from git..."

# Stash config.json changes if it exists and has local modifications
if [ -f config.json ] && ! git diff --quiet config.json 2>/dev/null; then
    echo "Stashing local config.json changes..."
    git stash push -m "Auto-stash config.json before update" config.json
    CONFIG_STASHED=true
else
    CONFIG_STASHED=false
fi

git pull

if [ $? -ne 0 ]; then
    echo "ERROR: Git pull failed"
    # Restore stashed config.json if pull failed
    if [ "$CONFIG_STASHED" = true ]; then
        echo "Restoring stashed config.json..."
        git stash pop 2>/dev/null || true
    fi
    exit 1
fi

# Restore stashed config.json after successful pull
if [ "$CONFIG_STASHED" = true ]; then
    echo "Restoring stashed config.json..."
    git stash pop 2>/dev/null || true
fi

echo "Git pull completed successfully"

# Step 2: Build Docker image
echo ""
echo "Building Docker image..."

echo "Region: ${AWS_DEFAULT_REGION:-us-west-2}"

# Build Docker image with build arguments
sudo docker build \
    --platform linux/amd64 \
    -t agent:latest .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "Docker image built successfully"

# Step 3: Run Docker container
echo ""
echo "Starting Docker container..."

# Stop all running containers
echo "Stopping all running Docker containers..."
sudo docker stop $(sudo docker ps -q) 2>/dev/null || true

# Remove all containers
echo "Removing all Docker containers..."
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true

# Capture repo dir for application volume mount (mirrors installer.py user-data)
REPO_DIR="$(pwd)"

# Run main Streamlit app container.
# Mount full host application/ so latest git-pulled code is always used,
# matching the behavior set up by installer.py.
sudo docker run -d \
    --platform linux/amd64 \
    --restart=always \
    --name agent-container \
    -p 8501:8501 \
    -v "$REPO_DIR/application:/app/application" \
    agent:latest

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start container"
    exit 1
fi

echo "Container started successfully"

# Step 4: Re-launch Telegram / Discord bot containers
# (installer.py launches these on initial provisioning; update.sh wiped them
# above, so we must restart them here using the same logic as the user-data
# script, otherwise the bots disappear after every update.)
echo ""
echo "Checking for bot configurations..."

CONFIG_FILE="$REPO_DIR/application/config.json"
if [ -f "$CONFIG_FILE" ]; then
    REGION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['region'])" 2>/dev/null || echo "")
    PROJECT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['projectName'])" 2>/dev/null || echo "")
else
    REGION=""
    PROJECT=""
    echo "WARN: $CONFIG_FILE not found; cannot start bot containers"
fi

if [ -n "$PROJECT" ] && [ -n "$REGION" ]; then
    # Telegram bot
    SECRET_ID="telegramapikey-$PROJECT"
    TG=$(sudo aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --region "$REGION" --query 'SecretString' --output text 2>/dev/null \
        | python3 -c 'import sys,json; s=sys.stdin.read().strip(); d=json.loads(s) if s else {}; print((d.get("telegram_api_key") or "").strip())' 2>/dev/null)
    if [ -n "$TG" ]; then
        echo "Starting Telegram bot..."
        sudo docker rm -f telegram-bot 2>/dev/null || true
        sudo docker run -d \
            --platform linux/amd64 \
            --restart=always \
            --name telegram-bot \
            --no-healthcheck \
            -w /app \
            -v "$REPO_DIR/application:/app/application" \
            --entrypoint python \
            agent:latest \
            application/telegram_bot.py
        echo "Telegram bot container started (sudo docker logs -f telegram-bot)"
    else
        echo "Telegram API key not set; skipping telegram-bot container"
    fi

    # Discord bot
    DISCORD_SECRET_ID="discordapikey-$PROJECT"
    DC=$(sudo aws secretsmanager get-secret-value --secret-id "$DISCORD_SECRET_ID" --region "$REGION" --query 'SecretString' --output text 2>/dev/null \
        | python3 -c 'import sys,json; s=sys.stdin.read().strip(); d=json.loads(s) if s else {}; print((d.get("discord_bot_token") or "").strip())' 2>/dev/null)
    if [ -n "$DC" ]; then
        echo "Starting Discord bot..."
        sudo docker rm -f discord-bot 2>/dev/null || true
        sudo docker run -d \
            --platform linux/amd64 \
            --restart=always \
            --name discord-bot \
            --no-healthcheck \
            -w /app \
            -v "$REPO_DIR/application:/app/application" \
            --entrypoint python \
            agent:latest \
            application/discord_bot.py
        echo "Discord bot container started (sudo docker logs -f discord-bot)"
    else
        echo "Discord bot token not set; skipping discord-bot container"
    fi
else
    echo "Could not determine project/region from config.json; skipping bot containers"
fi

echo ""
echo "Container status:"
sudo docker ps
echo ""
echo "To view logs:"
echo "  sudo docker logs agent-container"
echo "  sudo docker logs telegram-bot"
echo "  sudo docker logs discord-bot"

echo ""
echo "Update completed successfully!"

