# WhatsApp Templates API Endpoints

Complete documentation for the new WhatsApp templates endpoints.

## Base URL
```
https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net
```

## Authentication
All endpoints require one of the following:
- **JWT Token**: `Authorization: Bearer YOUR_JWT_TOKEN`
- **Service Key**: `X-Service-Key: YOUR_SERVICE_KEY`

All endpoints also require:
- **Tenant ID Header**: `X-Tenant-Id: your_tenant_id`

---

## Endpoints

### 1. Get All Templates

Fetches all WhatsApp message templates from Meta API for your WhatsApp Business Account.

**Endpoint:** `GET /templates/`

**Headers:**
```
X-Tenant-Id: ai
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "total_templates": 15,
  "waba_id": "123456789",
  "templates": [
    {
      "id": "1234567890",
      "name": "welcome_message",
      "language": "en",
      "status": "APPROVED",
      "category": "MARKETING",
      "components": [
        {
          "type": "HEADER",
          "format": "TEXT",
          "text": "Welcome!"
        },
        {
          "type": "BODY",
          "text": "Hello {{1}}, welcome to our service!"
        }
      ],
      "rejected_reason": null,
      "quality_score": {
        "score": "GREEN",
        "date": "2024-01-01"
      }
    }
  ]
}
```

**Features:**
- Fetches up to 1000 templates
- Results are cached for 5 minutes
- Includes template status, components, and quality scores

---

### 2. Get Template by Name

Get a specific template by its name.

**Endpoint:** `GET /templates/{template_name}`

**Example:** `GET /templates/welcome_message`

**Headers:**
```
X-Tenant-Id: ai
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "id": "1234567890",
  "name": "welcome_message",
  "language": "en",
  "status": "APPROVED",
  "category": "MARKETING",
  "components": [...],
  "rejected_reason": null,
  "quality_score": {...}
}
```

**Error Response (404):**
```json
{
  "detail": "Template 'xyz' not found"
}
```

---

### 3. Filter Templates by Status

Filter templates by their approval status.

**Endpoint:** `GET /templates/filter/by-status?status=APPROVED`

**Query Parameters:**
- `status` (string): Template status
  - Valid values: `APPROVED`, `PENDING`, `REJECTED`, `DISABLED`, `PAUSED`

**Headers:**
```
X-Tenant-Id: ai
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "status_filter": "APPROVED",
  "total_matching": 12,
  "templates": [...]
}
```

---

### 4. Refresh Templates Cache

Force refresh the templates cache by clearing it. Next request will fetch fresh data from Meta API.

**Endpoint:** `POST /templates/refresh`

**Headers:**
```
X-Tenant-Id: ai
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "message": "Templates cache cleared successfully",
  "tenant_id": "ai"
}
```

---

## Template Status Values

| Status | Description |
|--------|-------------|
| `APPROVED` | Template is approved and ready to use |
| `PENDING` | Template is awaiting Meta's approval |
| `REJECTED` | Template was rejected by Meta |
| `DISABLED` | Template has been disabled |
| `PAUSED` | Template is temporarily paused |

---

## Template Categories

| Category | Description |
|----------|-------------|
| `MARKETING` | Promotional content, offers, updates |
| `UTILITY` | Account updates, order updates, alerts |
| `AUTHENTICATION` | OTP codes, verification messages |

---

## Error Responses

### 400 - Missing Tenant ID
```json
{
  "detail": "Missing X-Tenant-Id header"
}
```

### 401 - Invalid Access Token
```json
{
  "detail": "Invalid or expired access token. Please reconnect your WhatsApp account."
}
```

### 403 - Permission Denied
```json
{
  "detail": "Access forbidden. Check your WhatsApp Business Account permissions."
}
```

### 404 - WhatsApp Account Not Found
```json
{
  "detail": "WhatsApp account not found for this tenant"
}
```

### 504 - Timeout
```json
{
  "detail": "Request timeout while fetching templates from WhatsApp"
}
```

---

## Example Usage

### JavaScript/Fetch
```javascript
// Get all templates
const response = await fetch('https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/', {
  headers: {
    'X-Tenant-Id': 'ai',
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  }
});

const data = await response.json();
console.log(`Found ${data.total_templates} templates`);
```

### cURL
```bash
# Get all templates
curl -X GET "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get specific template
curl -X GET "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/welcome_message" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Filter by status
curl -X GET "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/filter/by-status?status=APPROVED" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Refresh cache
curl -X POST "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/refresh" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Python
```python
import requests

headers = {
    'X-Tenant-Id': 'ai',
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
}

# Get all templates
response = requests.get(
    'https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/',
    headers=headers
)

templates = response.json()
print(f"Total templates: {templates['total_templates']}")

# Filter approved templates only
approved = requests.get(
    'https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/filter/by-status?status=APPROVED',
    headers=headers
).json()

print(f"Approved templates: {approved['total_matching']}")
```

---

## Caching Behavior

- Templates are cached for **5 minutes** after the first fetch
- Cache is per-tenant (different tenants have separate caches)
- Use `/templates/refresh` endpoint to force a fresh fetch
- Cache automatically expires and refetches after 5 minutes

---

## Notes

1. **Rate Limits**: Meta API has rate limits. Caching helps reduce API calls.
2. **Template Components**: Each template contains components (HEADER, BODY, FOOTER, BUTTONS)
3. **Quality Scores**: Meta provides quality scores (GREEN, YELLOW, RED) for templates
4. **Language Codes**: Templates use ISO 639-1 language codes (e.g., "en", "es", "hi")

---

## Testing

After restarting your FastAPI server, test the endpoint:

```bash
curl -X GET "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/templates/" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

If you get authentication errors, ensure:
1. Your JWT token is valid and not expired
2. The X-Tenant-Id header matches your tenant
3. Your WhatsApp access token in the database is still valid
