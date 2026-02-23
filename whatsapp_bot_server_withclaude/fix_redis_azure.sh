#!/bin/bash

# Fix Redis Connection in Azure App Service
# This script updates the REDIS_URL environment variable

echo "🔧 Fixing Redis connection for Azure deployment..."

# Variables
RESOURCE_GROUP="YOUR_RESOURCE_GROUP_NAME"  # UPDATE THIS
APP_NAME="YOUR_APP_SERVICE_NAME"           # UPDATE THIS (e.g., whatsappbotserver)
REDIS_URL="rediss://:O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM=@whatsappnuren.redis.cache.windows.net:6380"

echo "📋 Resource Group: $RESOURCE_GROUP"
echo "📋 App Service: $APP_NAME"
echo ""

# Update REDIS_URL environment variable
echo "⏳ Updating REDIS_URL in App Service settings..."
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --settings REDIS_URL="$REDIS_URL"

if [ $? -eq 0 ]; then
  echo "✅ REDIS_URL updated successfully"
else
  echo "❌ Failed to update REDIS_URL"
  exit 1
fi

# Restart App Service
echo ""
echo "⏳ Restarting App Service..."
az webapp restart \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME"

if [ $? -eq 0 ]; then
  echo "✅ App Service restarted successfully"
else
  echo "❌ Failed to restart App Service"
  exit 1
fi

echo ""
echo "🎉 Redis connection fix complete!"
echo ""
echo "📊 Verify by checking logs:"
echo "az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo ""
echo "Look for: '✅ Rate Limiter: Redis connected'"
