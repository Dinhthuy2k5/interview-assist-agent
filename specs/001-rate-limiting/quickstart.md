# Quickstart & Validation Guide: Sensitive API Rate Limiting

## 1. Prerequisites
- Backend test environment with Python 3.11
- Redis service running (or fakeredis for isolated unit tests)

## 2. Automated Test Execution
Run test suite verifying rate limiting:
```bash
cd backend
pytest tests/test_rate_limit.py -v
```

## 3. Manual Validation via cURL / HTTP Client

### Scenario A: Login Rate Limiting (5 requests / 60 seconds)
```bash
# Execute 6 rapid login requests with curl
for i in {1..6}; do
  curl -i -X POST http://localhost/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrongpassword"}'
done
```
**Expected Outcome**:
- First 5 requests return normal HTTP responses (401 Unauthorized or 200 OK).
- The 6th request immediately returns `HTTP/1.1 429 Too Many Requests` with:
  ```http
  Retry-After: <seconds>
  X-RateLimit-Limit: 5
  X-RateLimit-Remaining: 0
  ```

### Scenario B: AI Generation Rate Limiting (20 requests / 60 seconds)
Send rapid POST requests to `/api/questions/generate` using an authenticated Bearer token.
**Expected Outcome**:
- Blocked at request 21 with HTTP 429 without invoking external LLM APIs (Anthropic/Groq).
