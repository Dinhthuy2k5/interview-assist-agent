# Data Model & Storage Schema: Sensitive API Rate Limiting

## 1. Redis Key & State Design

Rate limit counters are stored entirely in Redis to guarantee statelessness across horizontally scaled backend workers.

### Key Naming Convention
```text
ratelimit:{scope}:{identifier}:{window_id}
```
- `{scope}`: The target action or route category (e.g., `login`, `ai_questions`, `ai_aggregation`, `audio_stt`).
- `{identifier}`: Either Client IP address (e.g., `192.168.1.50`) or User ID UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`).
- `{window_id}`: Integer timestamp bucket: `int(current_timestamp // window_seconds)`.

### Key Attributes
| Field / Property | Type | Description |
| :--- | :--- | :--- |
| **Value** | Integer (String in Redis) | Incremented count of requests made in the current window. |
| **TTL (Expiration)** | Seconds | Set to `window_seconds + 5` to ensure automatic memory cleanup after window closes. |

## 2. In-Memory Policy Model (Python Pydantic / Dataclass)

```python
class RateLimitConfig:
    requests: int        # Maximum number of requests allowed
    window: int          # Window size in seconds
    scope: str           # Unique identifier for endpoint category
    key_type: str        # "ip" or "user"
```

## 3. Rate Limit Response Headers (HTTP Contract)

| Header | Format | Example | Description |
| :--- | :--- | :--- | :--- |
| `X-RateLimit-Limit` | Integer | `5` | Maximum requests allowed in the window. |
| `X-RateLimit-Remaining` | Integer | `0` | Number of requests remaining in current window. |
| `X-RateLimit-Reset` | Integer (Epoch Unix seconds) | `1726588800` | Timestamp when current window resets. |
| `Retry-After` | Integer (Seconds) | `42` | Seconds until client can retry (only present on HTTP 429). |
