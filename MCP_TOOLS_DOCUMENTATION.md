# MCP Tools System Documentation

## Overview

The MCP (Model Context Protocol) Tools system allows clients to register custom API tools that get called automatically based on chat context for customer support and nurturing workflows.

## Architecture

```
WhatsApp Cloud API
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Node.js Webhook Server                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MCP Tool Router                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Keyword      │  │ Intent       │  │ LLM Function │ │ │
│  │  │ Matcher      │──│ Matcher      │──│ Calling      │ │ │
│  │  │ (< 5ms)      │  │ (< 10ms)     │  │ (fallback)   │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│ Redis Cache  │        │ Client APIs  │
│ (Tools +     │        │ (External)   │
│  Results)    │        └──────────────┘
└──────────────┘
        │
        ▼
┌──────────────┐        ┌──────────────┐
│ FastAPI      │◄──────►│ PostgreSQL   │
│ (Tool CRUD)  │        │ (Persistence)│
└──────────────┘        └──────────────┘
```

## Components

### FastAPI Module (`fastAPIWhatsapp_withclaude/mcp_tools/`)

- **models.py**: Database models for `MCPToolDefinition` and `MCPToolExecution`
- **schema.py**: Pydantic schemas for API request/response validation
- **router.py**: REST API endpoints for CRUD operations

### Node.js Services (`whatsapp_bot_server_withclaude/services/`)

- **mcpToolRouter.js**: Main entry point for tool evaluation
- **mcpToolCache.js**: Redis caching for tool definitions and results
- **mcpToolExecutor.js**: HTTP client for executing tool API calls
- **mcpLLMSelector.js**: AI provider function calling for fallback selection

## API Endpoints

### Tool Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mcp-tools` | List all tools for tenant |
| GET | `/mcp-tools/{tool_id}` | Get specific tool |
| POST | `/mcp-tools` | Create new tool |
| PUT | `/mcp-tools/{tool_id}` | Update tool |
| DELETE | `/mcp-tools/{tool_id}` | Delete tool |
| PATCH | `/mcp-tools/{tool_id}/toggle` | Toggle active status |
| POST | `/mcp-tools/{tool_id}/test` | Test tool execution |

### For Node.js

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mcp-tools/tenant/{tenant_id}` | Get all active tools (for caching) |
| POST | `/mcp-tools/executions` | Log tool execution |
| GET | `/mcp-tools/executions/tenant/{tenant_id}` | Get execution logs |

## Tool Configuration

### Example: Order Status Check

```json
{
  "name": "check_order_status",
  "description": "Check the delivery status of a customer order using order ID",
  "endpoint_url": "https://api.example.com/orders/${order_id}/status",
  "http_method": "GET",
  "auth_type": "bearer",
  "auth_config": {
    "token": "your-api-token"
  },
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "The order ID to check"
      }
    },
    "required": ["order_id"]
  },
  "trigger_keywords": ["order", "tracking", "delivery", "where is my"],
  "trigger_intents": ["check_status", "track_order"],
  "response_template": "Your order {{order_id}} is {{status}}. Expected delivery: {{eta}}",
  "error_template": "Sorry, I couldn't find that order. Please check the order ID and try again.",
  "cache_ttl_seconds": 30,
  "timeout_seconds": 10,
  "priority": 10
}
```

### Example: Book Appointment

```json
{
  "name": "book_appointment",
  "description": "Schedule an appointment for customer",
  "endpoint_url": "https://api.example.com/appointments",
  "http_method": "POST",
  "auth_type": "api_key",
  "auth_config": {
    "header": "X-API-Key",
    "key": "your-api-key"
  },
  "parameters": {
    "type": "object",
    "properties": {
      "service": {
        "type": "string",
        "enum": ["consultation", "demo", "support"]
      },
      "date": {
        "type": "string",
        "format": "date"
      },
      "time": {
        "type": "string"
      }
    },
    "required": ["service", "date"]
  },
  "trigger_keywords": ["book", "schedule", "appointment", "meeting"],
  "response_template": "Appointment booked for {{date}} at {{time}}. Confirmation: {{confirmation_id}}",
  "cache_ttl_seconds": 0,
  "priority": 5
}
```

### Example: Escalate to Human

```json
{
  "name": "escalate_to_human",
  "description": "Transfer conversation to a human agent",
  "endpoint_url": "https://api.example.com/escalations",
  "http_method": "POST",
  "trigger_keywords": ["human", "agent", "real person", "speak to someone", "talk to agent"],
  "response_template": "Connecting you to an agent. Ticket #{{ticket_id}}. Wait time: ~{{wait_minutes}} min",
  "priority": 100
}
```

## Environment Variables

### Node.js Server

```bash
# FastAPI connection
FASTAPI_URL=http://localhost:8000
FASTAPI_SERVICE_KEY=your-service-key
NODEJS_SERVICE_KEY=your-service-key

# Redis (for caching)
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# AI provider (for LLM fallback)
AI_API_KEY=sk-your-api-key
MCP_LLM_MODEL=gpt-4o-mini
MCP_LLM_TIMEOUT=10000

# Feature flags
MCP_ENABLE_LLM_FALLBACK=true
```

### FastAPI Server

```bash
# Service authentication
NODEJS_SERVICE_KEY=your-service-key
```

## Speed Optimizations

| Technique | Latency Saved | Implementation |
|-----------|---------------|----------------|
| Keyword matching first | ~500ms | Skip LLM for obvious intents |
| Tool definitions cache | ~50ms | Redis 5-min TTL |
| Result caching | ~200-2000ms | Per-tool configurable TTL |
| Connection pooling | ~30ms | axios keepAlive=true |

### Expected Latency

- **Keyword match + cached result**: < 20ms
- **Keyword match + API call**: 100-500ms (depends on client API)
- **LLM fallback + API call**: 600-1500ms

## Session Configuration

MCP tools can be configured per-session:

```javascript
// In userSession object
userSession.mcpToolsEnabled = true;    // Enable/disable MCP tools
userSession.mcpUseLLMFallback = true;  // Enable/disable LLM fallback
userSession.mcpToolResult = { ... };   // Last tool execution result
```

## Database Migration

Run the following to create the new tables:

```sql
-- Tool definitions table
CREATE TABLE IF NOT EXISTS mcp_tool_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenant_tenant(id),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL DEFAULT 'GET',
    auth_type VARCHAR(20) NOT NULL DEFAULT 'none',
    auth_config JSON,
    parameters JSON,
    headers JSON,
    request_body_template TEXT,
    trigger_keywords JSON,
    trigger_intents JSON,
    response_template TEXT,
    error_template TEXT,
    cache_ttl_seconds INTEGER DEFAULT 0,
    timeout_seconds INTEGER NOT NULL DEFAULT 10,
    retry_count INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_mcp_tools_tenant ON mcp_tool_definitions(tenant_id);
CREATE INDEX idx_mcp_tools_active ON mcp_tool_definitions(tenant_id, is_active);

-- Execution logs table
CREATE TABLE IF NOT EXISTS mcp_tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id UUID NOT NULL REFERENCES mcp_tool_definitions(id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    message_text TEXT,
    trigger_type VARCHAR(20) NOT NULL,
    request_params JSON,
    request_url VARCHAR(500),
    response_data JSON,
    response_message TEXT,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    from_cache BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mcp_executions_tool ON mcp_tool_executions(tool_id);
CREATE INDEX idx_mcp_executions_tenant ON mcp_tool_executions(tenant_id);
CREATE INDEX idx_mcp_executions_phone ON mcp_tool_executions(contact_phone);
CREATE INDEX idx_mcp_executions_created ON mcp_tool_executions(created_at);
```

## Testing

### 1. Create a Tool via API

```bash
curl -X POST "http://localhost:8000/mcp-tools" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: your-tenant-id" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "name": "check_order_status",
    "description": "Check order delivery status",
    "endpoint_url": "https://api.example.com/orders/${order_id}/status",
    "http_method": "GET",
    "trigger_keywords": ["order", "tracking", "delivery"],
    "response_template": "Your order {{order_id}} is {{status}}"
  }'
```

### 2. Test the Tool

```bash
curl -X POST "http://localhost:8000/mcp-tools/{tool_id}/test" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: your-tenant-id" \
  -d '{
    "params": {"order_id": "ORD12345"},
    "message_text": "Where is my order ORD12345?"
  }'
```

### 3. Send a WhatsApp Message

Send "Where is my order ORD12345?" to your WhatsApp bot. The MCP system should:
1. Match the keyword "order"
2. Extract the order_id "ORD12345"
3. Call the configured API
4. Return the formatted response

## Troubleshooting

### Tools Not Being Matched

1. Check if tools are active: `GET /mcp-tools?is_active=true`
2. Verify keywords are lowercase (they're auto-converted on save)
3. Check Redis connection for caching issues
4. Review logs for `[MCP Router]` entries

### API Calls Failing

1. Test the tool manually: `POST /mcp-tools/{tool_id}/test`
2. Check auth configuration
3. Verify endpoint URL template syntax (`${var}` for URL params)
4. Check timeout settings

### LLM Fallback Not Working

1. Verify `AI_API_KEY` is set
2. Check `MCP_ENABLE_LLM_FALLBACK` is not `false`
3. Ensure session has `mcpUseLLMFallback !== false`

## Files Reference

| File | Purpose |
|------|---------|
| `fastAPIWhatsapp_withclaude/mcp_tools/models.py` | Database models |
| `fastAPIWhatsapp_withclaude/mcp_tools/schema.py` | Pydantic schemas |
| `fastAPIWhatsapp_withclaude/mcp_tools/router.py` | CRUD API endpoints |
| `fastAPIWhatsapp_withclaude/main.py` | Router registration |
| `whatsapp_bot_server_withclaude/services/mcpToolRouter.js` | Main routing logic |
| `whatsapp_bot_server_withclaude/services/mcpToolCache.js` | Redis caching |
| `whatsapp_bot_server_withclaude/services/mcpToolExecutor.js` | HTTP executor |
| `whatsapp_bot_server_withclaude/services/mcpLLMSelector.js` | AI provider fallback |
| `whatsapp_bot_server_withclaude/mainwebhook/userWebhook.js` | Integration point |
| `nov2025/whatsapp_latest_final/helpers/vectorize.py` | Django AI mode with tools |

## AI Mode Integration (RAG + MCP Tools)

In addition to the pre-message keyword/intent matching, MCP tools can also be integrated into the AI conversation mode where users chat with AI provider using RAG (Retrieval Augmented Generation) data.

### How It Works

When a user is in AI mode and sends a message:

1. **RAG Context**: FAISS retrieves similar chunks from the tenant's document
2. **Tool Loading**: Active MCP tools are fetched for the tenant
3. **AI provider Function Calling**: The query is sent to AI provider with both:
   - The RAG context (similar document chunks)
   - MCP tools converted to AI provider function format
4. **Intelligent Decision**: AI provider decides whether to:
   - Answer directly from the RAG context
   - Call an MCP tool for real-time data
   - Combine both sources in the response
5. **Tool Execution**: If a tool is called, it's executed and the result is incorporated
6. **Response**: Final response is sent to the user

### Django Endpoint

A new endpoint `/query-faiss-with-tools/` has been added that extends the original `/query-faiss/` endpoint:

```python
# Request
POST /query-faiss-with-tools/
Headers:
  X-Tenant-Id: your-tenant-id
Body:
{
  "query": "What are your business hours and check my order ORD123?",
  "phone": "+1234567890",
  "nodes": [...],
  "language": "English",
  "use_tools": true
}

# Response
{
  "status": 200,
  "message": "Our business hours are 9 AM to 6 PM. Your order ORD123 is currently out for delivery and expected to arrive by 3 PM today.",
  "id": "node_id or -1",
  "tool_execution": {
    "tool_name": "check_order_status",
    "tool_args": {"order_id": "ORD123"},
    "tool_success": true
  }
}
```

### Node.js Integration

The `handleQuery()` function in `userWebhook.js` automatically uses the new endpoint when MCP tools are enabled:

```javascript
// Control via session configuration
userSession.mcpToolsInAIMode = true;  // Enable tools in AI mode (default: true)
userSession.mcpToolsInAIMode = false; // Disable tools, use original endpoint
```

### Environment Variables for Django

Add to your Django environment:

```bash
# FastAPI URL for fetching MCP tools
FASTAPI_BASE_URL=http://localhost:8000

# AI provider (already configured)
AI_API_KEY=sk-your-api-key
```

### Example Use Cases

**Hybrid Query**: User asks about both document content AND real-time data:
- User: "What's your return policy and where is my order #123?"
- AI: Retrieves return policy from RAG + calls order status tool
- Response combines both: "Our return policy allows 30 days... Your order #123 is currently in transit..."

**Tool-Only Query**: User asks for data the AI needs to fetch:
- User: "Book an appointment for tomorrow at 2pm"
- AI: Recognizes need for booking tool, calls it with extracted parameters
- Response: "I've booked your appointment for tomorrow at 2:00 PM. Confirmation: APT-456"

**RAG-Only Query**: User asks about document content:
- User: "What features does your premium plan include?"
- AI: Answers directly from RAG context without calling tools
- Response: "Our premium plan includes..."

### Files Added/Modified for AI Mode

| File | Changes |
|------|---------|
| `nov2025/whatsapp_latest_final/helpers/vectorize.py` | Added `query_with_tools()` endpoint and helper functions |
| `nov2025/whatsapp_latest_final/simplecrm/urls.py` | Added route for `/query-faiss-with-tools/` |
| `whatsapp_bot_server_withclaude/mainwebhook/userWebhook.js` | Modified `handleQuery()` to use new endpoint |

### Key Functions in vectorize.py

```python
# Fetch tools from FastAPI
get_mcp_tools_for_tenant(tenant_id) -> List[dict]

# Convert to AI provider function format
convert_tools_to_provider_functions(tools) -> List[dict]

# Execute tool API call
execute_mcp_tool(tool, params) -> dict

# AI provider call with function calling
get_provider_response_with_tools(query, context, user_data, language, prompt, tools)

# Main endpoint
query_with_tools(request) -> JsonResponse
```
