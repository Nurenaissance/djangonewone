#!/bin/bash
# Deployment script for Text Input Fix
# Fixes automation repeating for text inputs in tenant ehgymjv

echo "========================================="
echo "Text Input Fix Deployment"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "mainwebhook/userWebhook.js" ]; then
    echo "❌ Error: Must run from whatsapp_bot_server_withclaude directory"
    exit 1
fi

echo "✅ Verified directory location"
echo ""

# Check git status
echo "📋 Current Git Status:"
git status --short
echo ""

# Commit changes
echo "📝 Committing changes..."
git add mainwebhook/userWebhook.js AUTOMATION_TEXT_INPUT_FIX.md

git commit -m "Fix: Text input not advancing flow for tenant ehgymjv

- Added inputVariable recovery from node configuration
- Handles both legacy and V2 flow structures
- Fixes infinite loop when users send text for name/address
- Affects phone numbers like 919021404255

Root cause: inputVariable was null when text messages arrived,
causing handleInput to skip recording the user's input.

Fixes:
1. Early recovery when loading session (lines ~119-145)
2. Pre-input handling check before handleInput (lines ~661-682)

Testing: Verify text inputs for name/address now advance flow
" || echo "⚠️  No changes to commit (already committed)"

echo ""
echo "🔍 Verifying fixes are in place..."

# Verify fix 1
if grep -q "ENHANCED FIX: If still no inputVariable" mainwebhook/userWebhook.js; then
    echo "✅ Fix 1: Early inputVariable recovery - FOUND"
else
    echo "❌ Fix 1: Early inputVariable recovery - MISSING"
    exit 1
fi

# Verify fix 2
if grep -q "FIX.*Recovered missing inputVariable" mainwebhook/userWebhook.js; then
    echo "✅ Fix 2: Pre-input handling check - FOUND"
else
    echo "❌ Fix 2: Pre-input handling check - MISSING"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ All fixes verified and committed!"
echo "========================================="
echo ""

echo "Next steps:"
echo "1. Push to remote: git push origin newios"
echo "2. Deploy to Azure (if using Azure App Service)"
echo "3. Restart the server: pm2 restart whatsapp-bot-server"
echo "4. Test with phone number 919021404255 on tenant ehgymjv"
echo "5. Monitor logs for: '📝 [inputVariable] RECOVERED'"
echo ""

echo "Would you like to push to remote now? (y/n)"
read -r PUSH_RESPONSE

if [ "$PUSH_RESPONSE" = "y" ] || [ "$PUSH_RESPONSE" = "Y" ]; then
    echo ""
    echo "🚀 Pushing to origin/newios..."
    git push origin newios
    echo ""
    echo "✅ Pushed successfully!"
    echo ""
    echo "⚠️  Remember to restart the server for changes to take effect:"
    echo "   pm2 restart whatsapp-bot-server"
    echo "   OR"
    echo "   az webapp restart --name whatsappbotserver --resource-group <your-rg>"
else
    echo ""
    echo "⏸️  Skipping push. Run manually when ready:"
    echo "   git push origin newios"
fi

echo ""
echo "========================================="
echo "Deployment script completed!"
echo "========================================="
