# PowerShell Script to Upload All Environment Variables to Azure App Service
# This reads your .env file and uploads all variables to Azure

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================
$RESOURCE_GROUP = "YOUR_RESOURCE_GROUP_NAME"  # e.g., "whatsapp-rg"
$APP_NAME = "YOUR_APP_SERVICE_NAME"           # e.g., "whatsappbotserver"

Write-Host "🚀 Azure Environment Variables Upload Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Resource Group and App Name are set
if ($RESOURCE_GROUP -eq "YOUR_RESOURCE_GROUP_NAME" -or $APP_NAME -eq "YOUR_APP_SERVICE_NAME") {
    Write-Host "❌ ERROR: Please update RESOURCE_GROUP and APP_NAME in this script first!" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 To find your values, run:" -ForegroundColor Yellow
    Write-Host "   az webapp list --query ""[].{name:name, resourceGroup:resourceGroup}"" -o table" -ForegroundColor Yellow
    exit 1
}

Write-Host "📋 Resource Group: $RESOURCE_GROUP" -ForegroundColor Green
Write-Host "📋 App Service: $APP_NAME" -ForegroundColor Green
Write-Host ""

# Check if .env file exists
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "❌ ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "   Make sure you're running this from the whatsapp_bot_server_withclaude directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found .env file" -ForegroundColor Green
Write-Host ""

# Read .env file and convert to Azure format
Write-Host "⏳ Reading environment variables from .env..." -ForegroundColor Yellow

$envVars = @()
$multilineVar = $null
$multilineContent = ""

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()

    # Skip empty lines and comments
    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }

    # Handle multi-line values (enclosed in quotes)
    if ($multilineVar) {
        $multilineContent += "`n$line"
        if ($line.EndsWith('"')) {
            # End of multi-line value
            $value = $multilineContent -replace '^"', '' -replace '"$', ''
            $envVars += "$multilineVar=`"$value`""
            $multilineVar = $null
            $multilineContent = ""
        }
        return
    }

    # Check if line contains KEY=VALUE
    if ($line -match '^([^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()

        # Skip if value is empty or a comment
        if ($value -eq "" -or $key.StartsWith("#")) {
            return
        }

        # Check for multi-line values
        if ($value.StartsWith('"') -and -not $value.EndsWith('"')) {
            $multilineVar = $key
            $multilineContent = $value
            return
        }

        # Remove quotes from single-line values
        $value = $value -replace '^"', '' -replace '"$', ''

        # Escape special characters for Azure
        $value = $value -replace '"', '\"'

        $envVars += "$key=`"$value`""
    }
}

Write-Host "✅ Found $($envVars.Count) environment variables" -ForegroundColor Green
Write-Host ""

# Show variables being uploaded (mask sensitive values)
Write-Host "📦 Variables to upload:" -ForegroundColor Cyan
$envVars | ForEach-Object {
    $pair = $_ -split "=", 2
    $key = $pair[0]
    $value = $pair[1]

    # Mask sensitive values
    if ($key -match "KEY|SECRET|PASSWORD|TOKEN") {
        Write-Host "   $key=***MASKED***" -ForegroundColor Gray
    } else {
        $displayValue = $value.Substring(0, [Math]::Min(50, $value.Length))
        if ($value.Length -gt 50) { $displayValue += "..." }
        Write-Host "   $key=$displayValue" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "⚠️  This will UPDATE all environment variables in Azure App Service" -ForegroundColor Yellow
Write-Host "⚠️  Existing variables not in .env will be KEPT" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Cancelled" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "⏳ Uploading environment variables to Azure..." -ForegroundColor Yellow

try {
    # Upload all variables at once
    $settingsString = $envVars -join " "

    az webapp config appsettings set `
        --resource-group $RESOURCE_GROUP `
        --name $APP_NAME `
        --settings $envVars 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Environment variables uploaded successfully!" -ForegroundColor Green
    } else {
        throw "Azure CLI command failed"
    }
} catch {
    Write-Host "❌ Failed to upload environment variables" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Restarting App Service..." -ForegroundColor Yellow

try {
    az webapp restart `
        --resource-group $RESOURCE_GROUP `
        --name $APP_NAME 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ App Service restarted successfully!" -ForegroundColor Green
    } else {
        throw "Azure CLI command failed"
    }
} catch {
    Write-Host "❌ Failed to restart App Service" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 All done!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Verify deployment:" -ForegroundColor Cyan
Write-Host "   az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ Look for: '✅ Rate Limiter: Redis connected'" -ForegroundColor Green
Write-Host "✅ Look for: 'Server is listening on port: 8080'" -ForegroundColor Green
