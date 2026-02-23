#!/bin/bash

# Bash Script to Upload All Environment Variables to Azure App Service
# This reads your .env file and uploads all variables to Azure

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================
RESOURCE_GROUP="YOUR_RESOURCE_GROUP_NAME"  # e.g., "whatsapp-rg"
APP_NAME="YOUR_APP_SERVICE_NAME"           # e.g., "whatsappbotserver"

echo "🚀 Azure Environment Variables Upload Script"
echo "============================================="
echo ""

# Check if Resource Group and App Name are set
if [ "$RESOURCE_GROUP" = "YOUR_RESOURCE_GROUP_NAME" ] || [ "$APP_NAME" = "YOUR_APP_SERVICE_NAME" ]; then
    echo "❌ ERROR: Please update RESOURCE_GROUP and APP_NAME in this script first!"
    echo ""
    echo "📋 To find your values, run:"
    echo "   az webapp list --query \"[].{name:name, resourceGroup:resourceGroup}\" -o table"
    exit 1
fi

echo "📋 Resource Group: $RESOURCE_GROUP"
echo "📋 App Service: $APP_NAME"
echo ""

# Check if .env file exists
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERROR: .env file not found!"
    echo "   Make sure you're running this from the whatsapp_bot_server_withclaude directory"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Read .env file and build settings array
echo "⏳ Reading environment variables from .env..."

SETTINGS=()
COUNT=0

# Read file line by line
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [ -z "$line" ] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # Extract KEY=VALUE
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        KEY="${BASH_REMATCH[1]}"
        VALUE="${BASH_REMATCH[2]}"

        # Remove leading/trailing whitespace
        KEY=$(echo "$KEY" | xargs)
        VALUE=$(echo "$VALUE" | xargs)

        # Skip if empty
        if [ -z "$VALUE" ]; then
            continue
        fi

        # Remove surrounding quotes if present
        VALUE="${VALUE#\"}"
        VALUE="${VALUE%\"}"

        # Add to settings array
        SETTINGS+=("${KEY}=${VALUE}")
        COUNT=$((COUNT + 1))
    fi
done < "$ENV_FILE"

echo "✅ Found $COUNT environment variables"
echo ""

# Show variables being uploaded (mask sensitive values)
echo "📦 Variables to upload:"
for setting in "${SETTINGS[@]}"; do
    KEY="${setting%%=*}"
    VALUE="${setting#*=}"

    # Mask sensitive values
    if [[ "$KEY" =~ (KEY|SECRET|PASSWORD|TOKEN) ]]; then
        echo "   $KEY=***MASKED***"
    else
        # Show first 50 chars
        DISPLAY_VALUE="${VALUE:0:50}"
        if [ ${#VALUE} -gt 50 ]; then
            DISPLAY_VALUE="${DISPLAY_VALUE}..."
        fi
        echo "   $KEY=$DISPLAY_VALUE"
    fi
done

echo ""
echo "⚠️  This will UPDATE all environment variables in Azure App Service"
echo "⚠️  Existing variables not in .env will be KEPT"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "⏳ Uploading environment variables to Azure..."

# Upload all variables at once
if az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings "${SETTINGS[@]}" > /dev/null 2>&1; then
    echo "✅ Environment variables uploaded successfully!"
else
    echo "❌ Failed to upload environment variables"
    exit 1
fi

echo ""
echo "⏳ Restarting App Service..."

if az webapp restart \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" > /dev/null 2>&1; then
    echo "✅ App Service restarted successfully!"
else
    echo "❌ Failed to restart App Service"
    exit 1
fi

echo ""
echo "🎉 All done!"
echo ""
echo "📊 Verify deployment:"
echo "   az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo ""
echo "✅ Look for: '✅ Rate Limiter: Redis connected'"
echo "✅ Look for: 'Server is listening on port: 8080'"
