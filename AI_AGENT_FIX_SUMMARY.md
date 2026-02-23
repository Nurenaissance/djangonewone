# AI Voice Agent Connection Fix

## Date: 2026-01-09

## Problem
The frontend voice agent (Realtime API) was failing to connect because:
1. The `/api/ephemeral` endpoint didn't exist in the backend
2. No API proxy was configured in the frontend
3. The frontend was calling a relative URL that resolved to the wrong location

## Solution Overview

### 1. Created Backend Endpoint for Ephemeral Keys

**File:** `whatsapp_bot_server_withclaude/routes/aiAgentRoute.js`

Created a new route that:
- Generates Realtime API ephemeral keys
- Uses the `AI_API_KEY` from environment variables
- Handles errors gracefully with user-friendly messages
- Returns ephemeral keys for client-side voice agent connections

**Endpoint:** `GET /api/ephemeral`

**Response:**
```json
{
  "key": "ephemeral_key_value_here"
}
```

**Error Responses:**
- `500` - AI provider API key not configured
- `401` - Invalid AI provider API key
- `403` - Insufficient permissions for Realtime API
- `429` - Rate limit exceeded

### 2. Registered Route in Backend

**File:** `whatsapp_bot_server_withclaude/routes/index.js`

Added the AI agent route to the route setup:
```javascript
import aiAgentRoutes from './aiAgentRoute.js';
app.use('/api', aiAgentRoutes);
```

### 3. Configured Frontend API Proxy

**File:** `whatsappBusinessAutomation_withclaude/vite.config.js`

Added Vite proxy configuration to forward `/api/*` requests to the Node.js backend:

```javascript
server: {
  proxy: {
    '/api': {
      target: process.env.VITE_NODEJS_URL || 'http://localhost:8080',
      changeOrigin: true,
      secure: false,
    }
  }
}
```

### 4. Updated Voice Agent Hook

**File:** `whatsappBusinessAutomation_withclaude/src/Pages/HomePage/hooks/useVoiceAgent.js`

Updated `fetchEphemeralKey()` to:
- Use relative URL in development (proxied by Vite)
- Use full backend URL in production
- Add better error handling and logging
- Check response status before parsing JSON

```javascript
const isDevelopment = import.meta.env.DEV;
const apiUrl = isDevelopment
  ? '/api/ephemeral'
  : `${import.meta.env.VITE_NODEJS_URL || 'https://whatsappbotserver.azurewebsites.net'}/api/ephemeral`;
```

## Environment Configuration

### Backend (.env file)

The backend already has AI provider API key configured:
```bash
AI_API_KEY=sk-your-api-key-here
```

**Location:** `whatsapp_bot_server_withclaude/.env`

### Frontend (.env file)

Ensure the frontend has the Node.js backend URL configured:
```bash
VITE_NODEJS_URL=http://localhost:8080  # Development
# or
VITE_NODEJS_URL=https://whatsappbotserver.azurewebsites.net  # Production
```

**Location:** `whatsappBusinessAutomation_withclaude/.env`

## How It Works

### Development Flow
1. User taps on AI agent avatar
2. Frontend calls `/api/ephemeral` (relative URL)
3. Vite proxy forwards request to `http://localhost:8080/api/ephemeral`
4. Backend generates ephemeral key using AI provider API
5. Frontend receives key and connects to Realtime API
6. Voice agent session starts

### Production Flow
1. User taps on AI agent avatar
2. Frontend calls full URL: `https://whatsappbotserver.azurewebsites.net/api/ephemeral`
3. Backend generates ephemeral key using AI provider API
4. Frontend receives key and connects to Realtime API
5. Voice agent session starts

## Testing Checklist

### Backend Testing

1. **Test endpoint directly:**
   ```bash
   curl http://localhost:8080/api/ephemeral
   ```

   Expected response:
   ```json
   {
     "key": "some_ephemeral_key_value"
   }
   ```

2. **Verify AI provider API key is set:**
   ```bash
   grep AI_API_KEY .env
   ```

3. **Check server logs for errors:**
   - Start server: `node server.js`
   - Watch for: `✅ AI agent route loaded` or similar

### Frontend Testing

1. **Start development server:**
   ```bash
   cd whatsappBusinessAutomation_withclaude
   npm run dev
   ```

2. **Open browser DevTools:**
   - Go to Network tab
   - Navigate to homepage with voice agent

3. **Test voice agent:**
   - Click on the AI avatar
   - Grant microphone permissions
   - Check Network tab for `/api/ephemeral` request
   - Verify it returns 200 OK with ephemeral key

4. **Check console for errors:**
   - Open Console tab
   - Should see: API configuration logs
   - Should NOT see: "Failed to fetch ephemeral key" errors

### Error Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| No AI provider API key | Returns 500 with "AI provider API key not configured" |
| Invalid API key | Returns 401 with "Invalid AI provider API key" |
| Network error | Shows chat interface as fallback |
| Microphone denied | Automatically switches to chat mode |

## Troubleshooting

### Issue: "Failed to connect to AI assistant"

**Possible causes:**
1. Backend server not running
2. AI provider API key not set or invalid
3. Proxy not configured correctly
4. CORS issues

**Solution:**
1. Check backend server is running: `http://localhost:8080`
2. Verify AI provider API key in `.env`
3. Restart both frontend and backend servers
4. Check browser console for specific error messages

### Issue: "No ephemeral key received"

**Possible causes:**
1. AI provider API returned error
2. Response format incorrect
3. Network timeout

**Solution:**
1. Check backend server logs
2. Test endpoint directly with curl
3. Verify AI provider API key permissions

### Issue: Proxy not working

**Possible causes:**
1. Vite config not loaded
2. Wrong target URL
3. Development server not restarted

**Solution:**
1. Restart Vite dev server
2. Clear browser cache
3. Check `vite.config.js` proxy settings

## Realtime API Information

### Model
- Using: `gpt-4o-realtime-preview-2024-12-17`
- Voice: `alloy` (configurable)

### Permissions Required
Your AI provider API key needs access to the Realtime API. This might require:
- GPT-4 API access
- Realtime API beta access
- Sufficient credits/quota

### Rate Limits
- Check your AI provider dashboard for rate limits
- The backend returns 429 error if rate limit is hit
- Frontend automatically falls back to chat mode

## Future Improvements

1. **Caching**: Cache ephemeral keys with expiration
2. **Connection Pooling**: Reuse connections when possible
3. **Retry Logic**: Automatic retry with exponential backoff
4. **Monitoring**: Add metrics for key generation success/failure
5. **Multiple Voices**: Allow user to select voice preference
6. **Session Management**: Better handling of long-running sessions

## Security Notes

- ✅ AI provider API key stored only in backend `.env`
- ✅ Ephemeral keys expire automatically
- ✅ No API key exposed to frontend
- ✅ Backend validates all requests
- ⚠️ Consider adding rate limiting per user
- ⚠️ Add authentication for production use

## Cost Considerations

Realtime API pricing:
- Charged per audio token
- Approximately $0.01-0.02 per minute of conversation
- Monitor usage in AI provider dashboard
- Consider implementing usage quotas per user

## Related Files

### Backend
- `routes/aiAgentRoute.js` - Ephemeral key endpoint
- `routes/index.js` - Route registration
- `.env` - AI provider API key configuration

### Frontend
- `src/Pages/HomePage/hooks/useVoiceAgent.js` - Voice agent logic
- `vite.config.js` - API proxy configuration
- `.env` - Backend URL configuration

## Support

If issues persist:
1. Check AI provider API dashboard for API status
2. Verify API key has Realtime API access
3. Test with a simple curl request first
4. Check both frontend and backend logs
5. Ensure all environment variables are set correctly
