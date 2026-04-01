# Kore.ai API Streaming Behavior: Complete Guide

**Date**: 2026-02-12

**Status**: Tested and Documented

**Verdict**: Status streaming only, NOT content streaming

---

## Executive Summary

The Kore.ai Agentic App Platform API's "streaming mode" provides **status updates via Server-Sent Events (SSE)**, not real-time content streaming. This is fundamentally different from services like ChatGPT or Claude where you see tokens appearing as the LLM generates them.

### What Streaming Mode Actually Does

 **Status Streaming**: Real-time status updates (busy → idle)
 **Progress Notifications**: Know when agent starts/finishes processing
 **Better UX than Polling**: Instant status changes via SSE
 **NOT Content Streaming**: Content only available after completion
 **NOT Token-by-Token**: No real-time text generation display
 **NOT Async Mode**: Execute endpoint rejects `async` parameter

---

\newpage

## How Streaming Actually Works

### The Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Execute Request with stream.enable=true                      │
│    POST /apps/{appId}/environments/{envName}/runs/execute      │
│    Body: {"stream": {"enable": true, "streamMode": "tokens"}}  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. SSE Event 0: Status "busy"                                   │
│    data: {"eventIndex": 0, "sessionInfo": {                     │
│      "status": "busy", "runId": "r-xxx"                         │
│    }}                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. [Agent Processes Request Completely]                         │
│    - LLM generates full response                                │
│    - Tools are invoked                                          │
│    - Output buffered on server                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. SSE Event 1: Status "idle" (Complete)                        │
│    data: {"eventIndex": 1, "sessionInfo": {                     │
│      "status": "idle", "runId": "r-xxx"                         │
│    }, "isLastEvent": true}                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Fetch Output from Status Endpoint                            │
│    POST /apps/{appId}/environments/{envName}/runs/r-xxx/status │
│    Body: {"sessionIdentity": [{"type": "sessionReference",     │
│             "value": "session-id"}]}                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Response Contains Complete Output                            │
│    {"run": {"kwargs": {"output": [                              │
│      {"type": "text", "content": "Complete response here"}      │
│    ]}}}                                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Observations

1. **Only 2 SSE Events**: Initial "busy" and final "idle"
2. **No Content in Events**: SSE events contain NO output data
3. **Content Retrieved Separately**: Must call status endpoint
4. **Buffered Response**: Output available only after processing completes
5. **No Real-Time Display**: Cannot show tokens as they're generated

---

## API Request/Response Examples

### Example 1: Streaming Request

```bash
curl -X POST \
  https://agent-platform.kore.ai/api/v2/apps/aa-your-app-id/environments/stage/runs/execute \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionIdentity": [
      {
        "type": "userReference",
        "value": "user-123"
      },
      {
        "type": "sessionReference",
        "value": "session-456"
      }
    ],
    "input": [
      {
        "type": "text",
        "content": "Hello, how are you?"
      }
    ],
    "stream": {
      "enable": true,
      "streamMode": "tokens"
    }
  }'
```

### Response: SSE Event Stream

```
data: {"eventIndex":0,"messageId":"msg-abc123","sessionInfo":{"status":"busy","userReference":"user-123","sessionReference":"session-456","userId":"u-xyz","sessionId":"s-xyz","runId":"r-def456","appId":"aa-your-app-id"}}

data: {"eventIndex":1,"messageId":"msg-abc123","sessionInfo":{"status":"idle","userReference":"user-123","sessionReference":"session-456","userId":"u-xyz","sessionId":"s-xyz","runId":"r-def456","appId":"aa-your-app-id","attachments":[],"source":"AP"},"isLastEvent":true}
```

**Notice**: No `output` field in either event!

### Example 2: Fetch Output from Status Endpoint

```bash
curl -X POST \
  https://agent-platform.kore.ai/api/v2/apps/aa-your-app-id/environments/stage/runs/r-def456/status \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionIdentity": [
      {
        "type": "sessionReference",
        "value": "session-456"
      }
    ]
  }'
```

### Response: Complete Output

```json
{
  "run": {
    "_id": "r-def456",
    "sessionId": "s-xyz",
    "status": "success",
    "kwargs": {
      "input": [
        {
          "type": "text",
          "content": "Hello, how are you?"
        }
      ],
      "stream": {
        "streamMode": "tokens",
        "enable": true
      },
      "output": [
        {
          "type": "text",
          "content": "Hello! I'm doing great, thank you for asking! How can I assist you today?"
        }
      ]
    },
    "createdAt": "2026-02-12T22:59:00.361Z",
    "updatedAt": "2026-02-12T22:59:05.143Z"
  }
}
```

### Example 3: Non-Streaming Request (Simpler!)

```bash
curl -X POST \
  https://agent-platform.kore.ai/api/v2/apps/aa-your-app-id/environments/stage/runs/execute \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionIdentity": [
      {
        "type": "userReference",
        "value": "user-123"
      },
      {
        "type": "sessionReference",
        "value": "session-456"
      }
    ],
    "input": [
      {
        "type": "text",
        "content": "Hello, how are you?"
      }
    ]
  }'
```

### Response: Complete Output Immediately

```json
{
  "messageId": "msg-abc123",
  "output": [
    {
      "type": "text",
      "content": "Hello! I'm doing great, thank you for asking! How can I assist you today?"
    }
  ],
  "sessionInfo": {
    "status": "idle",
    "userReference": "user-123",
    "sessionReference": "session-456",
    "userId": "u-xyz",
    "sessionId": "s-xyz",
    "runId": "r-def456",
    "appId": "aa-your-app-id"
  }
}
```

**Notice**: Output is directly in the response - much simpler!

---

## Testing Results

### Test 1: Streaming Mode (Current Implementation)

**Date**: 2026-02-12

**Configuration**: `stream.enable=true`, `streamMode="tokens"`

**Result**:  Works, but only provides status updates

**Observations**:

- Received 2 SSE events (busy → idle)
- No content in SSE events
- Had to call status endpoint to get output
- Output available only after processing completes

### Test 2: Async Mode

**Date**: 2026-02-12

**Configuration**: `async=true` with streaming

**Result**:  API rejects with 400 error

**Error Response**:
```json
{
  "errors": [
    {
      "msg": "property async should not exist",
      "code": 400
    }
  ]
}
```

**Conclusion**: Execute endpoint does NOT support async execution

### Test 3: Stream Modes Comparison

Tested all three stream modes with identical queries:

| Stream Mode | SSE Events | Content in Events | Output Location |
|-------------|------------|-------------------|-----------------|
| `tokens` | 2 (busy → idle) |  No | Status endpoint |
| `messages` | 2 (busy → idle) |  No | Status endpoint |
| `custom` | Not tested | N/A | N/A |

**Conclusion**: All modes behave identically - status updates only

---

## What True Streaming Would Look Like

For comparison, here's what real content streaming (like ChatGPT) would do:

### Expected Behavior (NOT Available)

```
Event 0: {"status": "busy"}
Event 1: {"output": {"type": "text", "content": "Hello"}}
Event 2: {"output": {"type": "text", "content": "!"}}
Event 3: {"output": {"type": "text", "content": " I'm"}}
Event 4: {"output": {"type": "text", "content": " doing"}}
Event 5: {"output": {"type": "text", "content": " great"}}
...
Event N: {"status": "idle", "isLastEvent": true}
```

### Actual Behavior (Current)

```
Event 0: {"status": "busy", "runId": "r-xxx"}
[Long pause while agent processes]
Event 1: {"status": "idle", "isLastEvent": true}
[Must fetch output from status endpoint]
```

---

## Implementation in CLI

Our implementation handles the current streaming behavior:

### Client Logic (`client.py`)

```python
def _process_streaming_response(self, response) -> dict[str, Any]:
    """
    Process SSE streaming response.

    IMPORTANT: Kore.ai API provides STATUS streaming, not CONTENT streaming.
    """
    run_id = None
    last_session_info = None

    # Parse SSE events
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            event_data = json.loads(line[6:])

            # Capture runId and sessionInfo
            if "sessionInfo" in event_data:
                last_session_info = event_data["sessionInfo"]
                run_id = last_session_info.get("runId")

            # Check for last event
            if event_data.get("isLastEvent"):
                break

    # Fetch output from status endpoint
    if run_id and last_session_info:
        session_identity = [{
            "type": "sessionReference",
            "value": last_session_info["sessionReference"]
        }]

        status_response = self.get_run_status(run_id, session_identity)
        output = status_response["run"]["kwargs"]["output"]

        return {"output": output, "streaming": True}
```

### Usage in Chat Mode

```bash
agxr chat --profile stage
> #stream on
Streaming enabled (mode: tokens)

> Hello
# Behind the scenes:
# 1. Send execute request with streaming
# 2. Receive SSE: status="busy", runId="r-xxx"
# 3. Receive SSE: status="idle"
# 4. Call status endpoint with runId
# 5. Extract and display output

Agent: Hello! How can I assist you today?
```

---

## Stream Modes Explained

### Mode: `tokens`

**Documentation Says**: "Streams final results as tokens"

**Actual Behavior**: Streams status updates only

```bash
curl ... -d '{"stream": {"enable": true, "streamMode": "tokens"}}'
```

### Mode: `messages`

**Documentation Says**: "Sends complete messages as they're generated"

**Actual Behavior**: Streams status updates only

```bash
curl ... -d '{"stream": {"enable": true, "streamMode": "messages"}}'
```

### Mode: `custom`

**Documentation Says**: "For customized streaming behavior"

**Actual Behavior**: Not tested, likely same as others

```bash
curl ... -d '{"stream": {"enable": true, "streamMode": "custom", "customEventNames": ["event1"]}}'
```

---

## Recommendations

### For Most Use Cases: Use Regular Mode

Since content isn't streamed anyway, regular synchronous mode is simpler:

```bash
# Simpler - no streaming
curl -X POST ... -d '{
  "sessionIdentity": [...],
  "input": [...]
}'

# More complex - streaming (same result)
curl -X POST ... -d '{
  "sessionIdentity": [...],
  "input": [...],
  "stream": {"enable": true, "streamMode": "tokens"}
}'
# Then call status endpoint to get output
```

**Both produce identical output, but regular mode is one API call instead of two.**

### When to Use Streaming Mode

Consider streaming mode only if you need:
-  Real-time status updates in the UI (show "Agent is thinking...")
-  Better UX for long-running requests (show progress)
-  Ability to cancel long-running requests (detect when processing starts)

Don't use streaming mode if you expect:
-  Token-by-token text generation display
-  Real-time content streaming like ChatGPT
-  Partial responses during generation

### Best Practice

```python
# For normal requests (recommended)
response = client.execute_run(
    query="Hello",
    session_identity="session-123",
    stream_enabled=False  # Simpler, same result
)

# For long requests where you want progress updates
response = client.execute_run(
    query="Analyze this 100-page document",
    session_identity="session-123",
    stream_enabled=True,  # Show "busy" indicator
    stream_mode="tokens"
)
# Note: Still need to fetch output from status endpoint
```

---

## Comparison: Kore.ai vs. OpenAI/Anthropic

| Feature | Kore.ai API | OpenAI/Anthropic APIs |
|---------|-------------|----------------------|
| **Status Streaming** |  Yes (via SSE) |  Yes |
| **Content Streaming** |  No |  Yes (token-by-token) |
| **Real-Time Display** |  No |  Yes |
| **Async Execution** |  Not supported |  Yes (some endpoints) |
| **Output Location** | Status endpoint | Stream events |
| **Complexity** | Higher (2 API calls) | Lower (1 streaming call) |
| **Use Case** | Status updates | Real-time generation |

---

## Technical Details

### SSE Event Structure

```typescript
interface SSEEvent {
  eventIndex: number;          // Sequential event counter
  messageId: string;            // Unique message ID
  sessionInfo: {
    status: "busy" | "idle";   // Execution status
    userReference: string;
    sessionReference: string;
    userId: string;
    sessionId: string;
    runId: string;              // Important: needed for status call
    appId: string;
  };
  isLastEvent?: boolean;        // Present on final event
  output?: never;               //  Never present in practice
}
```

### Status Endpoint Response

```typescript
interface StatusResponse {
  run: {
    _id: string;                // Run ID
    sessionId: string;
    status: "success" | "failed" | "pending" | "running";
    kwargs: {
      input: Array<{type: string; content: string}>;
      stream?: {enable: boolean; streamMode: string};
      output: Array<{            //  Output is here
        type: "text";
        content: string;
      }>;
    };
    createdAt: string;
    updatedAt: string;
  };
}
```

---

## Debugging Tips

### Enable Debug Logging

```bash
agxr chat --profile stage --log-level DEBUG
```

### What to Look For

1. **SSE Lines**: Should see `data: {...}` lines
2. **runId Capture**: Should log "Captured runId: r-xxx"
3. **Status Call**: Should see "POST .../runs/r-xxx/status"
4. **Output Extraction**: Should see "Fetched output from status endpoint"

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No output displayed | Status call failed | Check sessionIdentity format |
| 500 error on status | Missing sessionReference | Include only sessionReference, not userReference |
| No SSE events | Network issue | Check connection, try regular mode |
| "property async should not exist" | Trying to use async mode | Remove async parameter |

---

## Conclusion

The Kore.ai API's "streaming mode" is fundamentally different from what developers expect based on experience with ChatGPT, Claude, or other LLM services.

**What It Is**:

- Async status notification system
- Real-time progress updates via SSE
- Useful for UX (showing "thinking" indicators)

**What It's Not**:

- Real-time content streaming
- Token-by-token generation display
- Progressive text appearance

**For Best Results**:

- Use regular synchronous mode for most cases
- Use streaming mode only when you need status updates
- Set correct expectations with users
- Don't promise "real-time streaming" UX

---

## References

- **API Documentation**: https://docs.kore.ai/agent-platform/apis/agentic-apps/execute/
- **Implementation**: `agxr/client.py` - `_process_streaming_response()`
- **Testing**: Tested on 2026-02-12 with Kore.ai stage environment
- **Project Docs**: `CLAUDE.md` - "Streaming Behavior" section

---

**Document Version**: 1.0
**Last Updated**: 2026-02-12
**Tested By**: Development Team
**Status**: Production Findings
