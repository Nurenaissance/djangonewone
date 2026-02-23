# Access Token Security Fix - Documentation

## Overview
This document describes the security fix implemented to prevent exposing WhatsApp API access tokens to the frontend.

## Problem
The `/whatsapp_tenant` API endpoint was returning `access_token` in the response, which was being used by frontend code to make direct calls to Facebook Graph API. **This is a critical security vulnerability.**

## Changes Made

### 1. FastAPI Backend (`fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py`)

#### Change #1: Remove `access_token` from Response (Line 188-195)
```python
# SECURITY: Remove access_token from response to frontend
# Access tokens should never be exposed to client-side code
whatsapp_data_safe = []
for data in whatsapp_data:
    data_dict = jsonable_encoder(data)
    # Remove sensitive fields
    data_dict.pop('access_token', None)
    whatsapp_data_safe.append(data_dict)
```

**Impact:** The `/whatsapp_tenant` endpoint NO LONGER returns `access_token` in the response.

#### Change #2: New Secure Proxy Endpoint (Line 1975-2050)
```python
@router.get("/template-analytics")
async def get_template_analytics(
    template_id: str,
    start: int,
    end: int,
    granularity: str = "daily",
    metric_types: str = "cost,clicked,delivered,read,sent",
    db: orm.Session = Depends(get_db),
    x_tenant_id: Optional[str] = Header(None)
):
```

**Purpose:** Secure backend proxy for Facebook Graph API calls. Frontend calls this instead of Facebook directly.

## What Will Break

### Frontend Files That Will Break:

1. **BroadcastHistory.jsx** (Lines 297, 455)
   - Currently makes direct Facebook API calls using `access_token`
   - **Error:** `responses.data.whatsapp_data[0].access_token` will be `undefined`

2. **ProfilePage.jsx** (Line 272)
   - Tries to set `accessToken` from response
   - **Error:** State will be `undefined`

3. **BroadcastPage.jsx** (Line 146)
   - Tries to set `accessToken` from response
   - **Error:** State will be `undefined`

4. **NodeTypes.jsx** (Lines 555, 1170)
   - Tries to set `accessToken` from response
   - **Error:** State will be `undefined`

5. **functionManager.jsx** (Line 25)
   - Tries to set `accessToken` from response
   - **Error:** State will be `undefined`

### What Won't Break:

- **Node.js Backend** (`whatsapp_bot_server_withclaude/routes/messageRoute.js:50`)
  - Still works because it calls FastAPI's `/whatsapp_tenant` endpoint directly (backend-to-backend)
  - Backend-to-backend calls should still have access to `access_token` if needed

## How to Fix the Frontend

### Option 1: Use the New Secure Proxy Endpoint (Recommended)

**For BroadcastHistory.jsx:**

Replace this:
```javascript
const response = await axios.get(
  `https://graph.facebook.com/v22.0/${responses.data.whatsapp_data[0].business_account_id}/template_analytics`,
  {
    headers: {
      Authorization: `Bearer ${responses.data.whatsapp_data[0].accessToken}`,
    },
    params: {
      access_token: responses.data.whatsapp_data[0].access_token,
      start: startDate,
      end: endDate,
      granularity: "daily",
      metric_types: "cost,clicked,delivered,read,sent",
      template_ids: [`${templateId}`],
    },
  }
);
```

With this:
```javascript
const response = await axios.get(
  `${import.meta.env.VITE_FASTAPI_URL}/whatsapp_tenant/template-analytics`,
  {
    headers: {
      "X-Tenant-Id": tenantId  // Add your tenant ID
    },
    params: {
      template_id: templateId,
      start: startDate,
      end: endDate,
      granularity: "daily",
      metric_types: "cost,clicked,delivered,read,sent"
    },
  }
);
```

### Option 2: Remove Unused Access Token References

For files that just store the access_token but don't use it (ProfilePage, BroadcastPage, NodeTypes, functionManager):

Simply remove the lines that try to access `access_token`:

```javascript
// DELETE THIS LINE:
setAccessToken(response.data.whatsapp_data[0].access_token);
```

If the component doesn't actually use the `accessToken` state, also remove the state declaration:

```javascript
// DELETE THIS LINE:
const [accessToken, setAccessToken] = useState(null);
```

## Testing Checklist

- [ ] Test `/whatsapp_tenant` endpoint - verify `access_token` is NOT in response
- [ ] Test BroadcastHistory page - analytics should still load via proxy
- [ ] Test ProfilePage - should load without errors
- [ ] Test BroadcastPage - should load without errors
- [ ] Test Flow builder (NodeTypes.jsx) - should work normally
- [ ] Test backend-to-backend calls (Node.js messageRoute.js) - should still have access

## Security Benefits

✅ **No sensitive tokens exposed to browser**
✅ **No tokens in browser DevTools/Network tab**
✅ **No tokens in frontend JavaScript**
✅ **Centralized access control** - backend validates all requests
✅ **Easier token rotation** - only backend code needs updating
✅ **Better audit trail** - all API calls logged on backend

## Rollback Instructions

If you need to rollback this change:

1. In `fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py` line 188-200, replace with:
```python
return {
    "whatsapp_data": jsonable_encoder(whatsapp_data),
    "agents": jsonable_encoder(tenant_data.agents),
    "triggers": node_template_data
}
```

2. Remove the new `/template-analytics` endpoint (lines 1971-2050)

**Note:** Rolling back re-introduces the security vulnerability!

## Next Steps

1. Update frontend code to use the new proxy endpoint
2. Remove all `access_token` references from frontend state management
3. Test all affected pages
4. Consider creating additional proxy endpoints for other Facebook API calls if needed
5. Deploy FastAPI changes first, then frontend changes

## Questions?

Contact the development team or refer to:
- [Facebook Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [OWASP Token Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
