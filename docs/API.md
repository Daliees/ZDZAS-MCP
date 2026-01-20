# ZDZAS-MCP API Documentation

## Overview

The Chat API provides REST endpoints for interacting with the ZAS agent. It supports streaming responses, conversation management, feedback collection, and Salesforce integration.

**Base URL**: `http://localhost:9000`

**Authentication**: Salesforce headers or Basic Auth (see [Authentication](#authentication))

---

## Endpoints

### 1. Health Check

#### `GET /ping`

Check if the API is running.

**Request:**
```bash
curl http://localhost:9000/ping \
  -u "username:password"
```

**Response:**
```json
true
```

**Status Codes:**
- `200` - API is healthy
- `403` - Unauthorized

---

### 2. Chat

#### `POST /chat`

Send a message to the ZAS agent and receive a response.

**Headers:**
- `Content-Type: application/json` (required)
- `X-Salesforce-Org-Id` (optional) - Salesforce organization ID
- `X-Salesforce-User-Id` (optional) - Salesforce user ID
- `X-Session-Id` (optional) - Session/conversation ID
- `X-Zas-Tenant-Id` (optional) - Tenant identifier
- `X-Zas-Url` (optional) - Current page URL
- `Authorization: Basic <credentials>` (optional, alternative auth)

**Request Body:**
```json
{
  "message": "What tickets are assigned to me?",
  "conversationId": "uuid-string-optional",
  "tenantId": "tenant-123",
  "url": "https://example.com/page",
  "salesforceContext": {
    "orgId": "00D...",
    "userId": "005...",
    "userName": "John Doe",
    "userEmail": "john@example.com"
  }
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message/question |
| `conversationId` | string | No | Conversation ID to maintain context |
| `tenantId` | string | No | Tenant identifier |
| `url` | string | No | Current page URL for context |
| `salesforceContext` | object | No | Salesforce user context |
| `salesforceContext.orgId` | string | No | Salesforce org ID |
| `salesforceContext.userId` | string | No | Salesforce user ID |
| `salesforceContext.userName` | string | No | User's display name |
| `salesforceContext.userEmail` | string | No | User's email address |

**Example Request:**
```bash
curl -X POST http://localhost:9000/chat \
  -H "Content-Type: application/json" \
  -H "X-Salesforce-Org-Id: 00D5g000000abcX" \
  -H "X-Salesforce-User-Id: 0055g000000ABCD" \
  -d '{
    "message": "Show me open tickets",
    "conversationId": "conv-123"
  }'
```

**Response:**
```json
{
  "reply": "Here are your open tickets:\n\n1. Ticket #12345: Login issue\n2. Ticket #12346: Password reset\n\nWould you like details on any of these?",
  "conversationId": "conv-123"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `reply` | string | Agent's response message |
| `conversationId` | string | ID for maintaining conversation context |

**Status Codes:**
- `200` - Success
- `403` - Unauthorized (missing/invalid auth)
- `500` - Internal server error

**Logged Data:**
- Request/response logged to database (`RequestLog`)
- Events logged to `logs/chat_events.jsonl`
- Entity extraction (orgs, users) stored in database

---

### 3. Feedback

#### `POST /feedback`

Submit user feedback on a chat response.

**Headers:**
- `Content-Type: application/json` (required)
- Authentication headers (see [Authentication](#authentication))

**Request Body:**
```json
{
  "conversationId": "conv-123",
  "requestId": "uuid-string",
  "rating": 5,
  "comment": "Very helpful response!",
  "createdAt": "2026-01-20T10:30:00Z"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversationId` | string | No | Associated conversation ID |
| `requestId` | string | No | Associated request ID |
| `rating` | integer | No | Rating 1-5 |
| `comment` | string | No | Free-text feedback |
| `createdAt` | datetime | Yes | Timestamp of feedback |

**Example Request:**
```bash
curl -X POST http://localhost:9000/feedback \
  -H "Content-Type: application/json" \
  -H "X-Salesforce-Org-Id: 00D5g000000abcX" \
  -H "X-Salesforce-User-Id: 0055g000000ABCD" \
  -d '{
    "conversationId": "conv-123",
    "rating": 5,
    "comment": "Perfect answer!",
    "createdAt": "2026-01-20T10:30:00Z"
  }'
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` - Feedback saved
- `403` - Unauthorized
- `500` - Failed to save feedback

**Logged To:**
- `zas_feedback_log.jsonl` (JSON Lines format)

---

### 4. Reset Conversation

#### `POST /reset`

Clear conversation history for a session.

**Headers:**
- `Content-Type: application/json` (required)
- `X-Session-Id` (optional) - Session to reset
- Authentication headers (see [Authentication](#authentication))

**Request Body:**
```json
{
  "conversationId": "conv-123"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversationId` | string | No | Conversation to reset (or use X-Session-Id header) |

**Example Request:**
```bash
curl -X POST http://localhost:9000/reset \
  -H "Content-Type: application/json" \
  -H "X-Salesforce-Org-Id: 00D5g000000abcX" \
  -H "X-Salesforce-User-Id: 0055g000000ABCD" \
  -d '{
    "conversationId": "conv-123"
  }'
```

**Response:**
```json
{
  "status": "ok"
}
```

or if no conversation ID provided:
```json
{
  "status": "ok",
  "message": "No conversation id provided"
}
```

**Status Codes:**
- `200` - Conversation reset
- `403` - Unauthorized

---

## Authentication

The API supports two authentication methods:

### 1. Salesforce Headers (Recommended)

Include both headers in your request:
```
X-Salesforce-Org-Id: <your-org-id>
X-Salesforce-User-Id: <your-user-id>
```

**Example:**
```bash
curl -X POST http://localhost:9000/chat \
  -H "X-Salesforce-Org-Id: 00D5g000000abcX" \
  -H "X-Salesforce-User-Id: 0055g000000ABCD" \
  -d '{"message": "Hello"}'
```

### 2. Basic Authentication

Use HTTP Basic Auth with username:password:
```
Authorization: Basic <base64-encoded-credentials>
```

**Default Credentials** (change in production):
- Username: `asFWdSA4scvgqHE0HkTM*BxGJ`
- Password: `FRtnFNmEYTDQACYzjpXdQsTGng0aSUzr9v`

**Example:**
```bash
curl -X POST http://localhost:9000/chat \
  -u "asFWdSA4scvgqHE0HkTM*BxGJ:FRtnFNmEYTDQACYzjpXdQsTGng0aSUzr9v" \
  -d '{"message": "Hello"}'
```

**⚠️ Security Warning**: Change default credentials in `src/zas/api/middleware.py` before production deployment.

---

## CORS Configuration

**Current Settings** (for development):
```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**⚠️ Production**: Restrict `allow_origins` to specific domains in `chat_api.py`:
```python
allow_origins=["https://yourdomain.com", "https://app.salesforce.com"]
```

---

## Error Responses

All errors return JSON with standard format:

```json
{
  "detail": "Error message"
}
```

### Common Error Codes

| Status | Meaning | Cause |
|--------|---------|-------|
| 403 | Forbidden | Missing or invalid authentication |
| 404 | Not Found | Endpoint doesn't exist |
| 422 | Unprocessable Entity | Invalid request body format |
| 500 | Internal Server Error | Server-side error (check logs) |

**Example 403 Error:**
```json
{
  "detail": "Unauthorized"
}
```

**Example 500 Error:**
```json
{
  "detail": "Internal ZAS error"
}
```

---

## Conversation Management

### Maintaining Context

To maintain conversation context across requests, include the same `conversationId`:

**First Request:**
```bash
curl -X POST http://localhost:9000/chat \
  -H "X-Salesforce-Org-Id: 00D..." \
  -H "X-Salesforce-User-Id: 005..." \
  -d '{"message": "Show me open tickets"}'
```

**Response:**
```json
{
  "reply": "You have 3 open tickets...",
  "conversationId": "generated-uuid-123"
}
```

**Follow-up Request (with context):**
```bash
curl -X POST http://localhost:9000/chat \
  -H "X-Salesforce-Org-Id: 00D..." \
  -H "X-Salesforce-User-Id: 005..." \
  -d '{
    "message": "Show me more details on the first one",
    "conversationId": "generated-uuid-123"
  }'
```

The agent will remember the previous conversation and understand "the first one" refers to the first ticket mentioned.

### Clearing Context

To start a fresh conversation, either:
1. Omit `conversationId` (new ID will be generated)
2. Call `/reset` endpoint with the conversation ID

---

## Logging

### Structured Logging

All requests are logged to `logs/chat_events.jsonl` in JSON Lines format:

```jsonl
{"event":"chat_request","requestId":"uuid","conversationId":"conv-123","message":"Hello","timestamp":"2026-01-20T10:30:00"}
{"event":"chat_response","requestId":"uuid","conversationId":"conv-123","tokensUsed":150,"replyLength":45,"timestamp":"2026-01-20T10:30:01"}
```

**Event Types:**
- `chat_request` - Incoming chat request
- `chat_response` - Successful response
- `chat_error` - Error during processing
- `chat_unauthorized` - Authentication failure

### Database Logging

Chat interactions are stored in SQLite database:

**Tables:**
- `request_log` - All requests and responses
- `entities` - Extracted organizations and users

**Schema (request_log):**
```sql
CREATE TABLE request_log (
    id INTEGER PRIMARY KEY,
    request_id VARCHAR(36),
    user_id VARCHAR(100),
    organisation_id VARCHAR(100),
    conversation_id VARCHAR(100),
    tenant_id VARCHAR(100),
    page_url TEXT,
    message TEXT,
    reply TEXT,
    tokens_used INTEGER,
    salesforce_org_id VARCHAR(100),
    salesforce_user_id VARCHAR(100),
    salesforce_user_name VARCHAR(200),
    error TEXT,
    created_at TIMESTAMP
);
```

---

## Rate Limiting

⚠️ **Not yet implemented**. For production, consider adding rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(...):
    ...
```

---

## Examples

### Python Example

```python
import requests

def chat_with_zas(message, conversation_id=None):
    url = "http://localhost:9000/chat"
    headers = {
        "X-Salesforce-Org-Id": "00D5g000000abcX",
        "X-Salesforce-User-Id": "0055g000000ABCD"
    }
    payload = {
        "message": message,
        "conversationId": conversation_id
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# Example usage
result = chat_with_zas("What are my open tickets?")
print(result["reply"])

# Follow-up with context
result = chat_with_zas(
    "Show me the first one", 
    conversation_id=result["conversationId"]
)
print(result["reply"])
```

### JavaScript/TypeScript Example

```typescript
interface ChatRequest {
  message: string;
  conversationId?: string;
}

interface ChatResponse {
  reply: string;
  conversationId: string;
}

async function chatWithZas(
  message: string, 
  conversationId?: string
): Promise<ChatResponse> {
  const response = await fetch('http://localhost:9000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Salesforce-Org-Id': '00D5g000000abcX',
      'X-Salesforce-User-Id': '0055g000000ABCD'
    },
    body: JSON.stringify({
      message,
      conversationId
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }
  
  return await response.json();
}

// Usage
const result = await chatWithZas("What are my open tickets?");
console.log(result.reply);
```

### Salesforce Lightning Web Component

See [docs/salesforce/QUICKSTART.md](salesforce/QUICKSTART.md) for full Salesforce integration.

**Example LWC:**
```javascript
import { LightningElement, track } from 'lwc';

export default class ZasChatUtility extends LightningElement {
    @track messages = [];
    conversationId;
    
    async sendMessage(messageText) {
        const response = await fetch('/services/apexrest/zaschat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: messageText,
                conversationId: this.conversationId
            })
        });
        
        const data = await response.json();
        this.conversationId = data.conversationId;
        this.messages.push({ text: data.reply, isAgent: true });
    }
}
```

---

## Monitoring & Observability

### Health Checks

```bash
# Simple health check
curl http://localhost:9000/ping

# Check with authentication
curl -X POST http://localhost:9000/chat \
  -H "X-Salesforce-Org-Id: test" \
  -H "X-Salesforce-User-Id: test" \
  -d '{"message": "test"}'
```

### Log Analysis

```bash
# View recent chat events
tail -f logs/chat_events.jsonl | jq

# Count requests by conversation ID
jq -r '.conversationId' logs/chat_events.jsonl | sort | uniq -c

# Find errors
jq 'select(.event=="chat_error")' logs/chat_events.jsonl

# Average tokens used
jq -s 'map(select(.tokensUsed)) | add / length' logs/chat_events.jsonl
```

---

## Troubleshooting

### Issue: 403 Forbidden

**Cause**: Missing or invalid authentication

**Solution**: Include either Salesforce headers or Basic Auth:
```bash
curl -H "X-Salesforce-Org-Id: xxx" -H "X-Salesforce-User-Id: yyy" ...
```

### Issue: 500 Internal Server Error

**Cause**: Server-side error (check logs)

**Solution**: 
1. Check `logs/chat_events.jsonl` for error details
2. Look at terminal output for stack traces
3. Verify environment variables in `.env`

### Issue: Empty or Incomplete Response

**Cause**: Token limit exceeded or agent error

**Solution**:
1. Check `tokensUsed` in logs
2. Simplify the question
3. Reset conversation with `/reset`

### Issue: Conversation Context Lost

**Cause**: Not passing `conversationId` correctly

**Solution**: Always include the conversation ID from previous response:
```json
{
  "message": "follow up question",
  "conversationId": "uuid-from-previous-response"
}
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [docs/salesforce/](salesforce/) - Salesforce integration documentation
- [MCP Tools Documentation](../README.md) - Available agent tools
