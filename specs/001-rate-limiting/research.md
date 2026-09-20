# Research & Technical Decisions: Sensitive API Rate Limiting

## Decision 1: Rate Limiting Algorithm & Redis Storage Strategy
- **Context**: The system must enforce rate limits across horizontally scaled FastAPI replicas (3 backend containers behind Traefik).
- **Options Evaluated**:
  1. *Token Bucket / Leaky Bucket (Lua Script)*: Complex to tune, higher memory overhead per bucket.
  2. *Sliding Window Log (ZSET)*: Exact to the millisecond, but requires storing every timestamp in a Redis sorted set; higher memory consumption under heavy traffic.
  3. *Fixed Window with Atomic Increment (INCR + EXPIRE)*: Extremely lightweight, O(1) time complexity, minimal Redis memory footprint. Can be extended to a 2-window sliding counter or simple fixed window with immediate TTL.
- **Decision**: Fixed window counter with atomic pipeline (`INCR` + conditional `EXPIRE`) partitioned by timestamp bucket (`rl:{scope}:{identifier}:{window_timestamp}`).
- **Rationale**:
  - Extremely fast (<1ms overhead in Redis).
  - Native atomic operations in Redis prevent race conditions without needing complex external distributed locks.
  - Automatically cleaned up by Redis native TTL.

## Decision 2: FastAPI Integration Pattern (Middleware vs Dependency)
- **Context**: Need to enforce different rate limits on specific routes (e.g., 5/min for login by IP, 20/min for AI generation by User ID).
- **Options Evaluated**:
  1. *Global Starlette Middleware*: Intercepts every single HTTP request. Harder to configure route-specific parameters and user-based keys before authentication dependencies resolve.
  2. *FastAPI Dependency Injection (`Depends(RateLimiter(...))`)*:
     - Natively integrates into route signatures.
     - Can access `Request`, authenticated user context (`current_user`), or client IP dynamically.
     - Reusable across any router.
     - Allows raising `HTTPException(status_code=429)` cleanly with custom response headers (`Retry-After`, `X-RateLimit-*`).
- **Decision**: FastAPI Dependency class `RateLimiter` placed in `app/core/rate_limit.py`.
- **Rationale**: Maximizes modularity, readability, and compatibility with FastAPI dependency resolution.

## Decision 3: Client Identity Extraction & Proxy Awareness
- **Context**: Backend instances run behind Traefik reverse proxy in Docker network.
- **Decision**:
  - For unauthenticated routes (e.g., login): Extract IP from `X-Forwarded-For` (first IP in chain) with fallback to `request.client.host`.
  - For authenticated routes (e.g., question generation, transcripts, aggregation): Extract user ID (`user.id`) if user is authenticated; fallback to IP if unauthenticated.
- **Rationale**: Prevents users from sharing rate limit buckets when accessing authenticated features from behind the same office NAT/VPN, while strictly bounding login attempts per IP.

## Decision 4: High Availability & Fail-Open Behavior
- **Context**: Principle IV & V in Constitution dictate high availability during live interviews. If Redis fails, should we block all requests or allow them through?
- **Decision**: Fail-open with warning log.
- **Rationale**: If Redis is temporarily down, blocking legitimate interviewers in the middle of a live interview session causes severe operational disruption. A security rate-limiter should degrade gracefully when secondary storage is unreachable.
