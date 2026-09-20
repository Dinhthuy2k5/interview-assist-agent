# Feature Specification: Sensitive API Rate Limiting

**Feature Branch**: `001-rate-limiting`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Implement Redis-based rate limiting on sensitive API endpoints"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Protection Against Brute Force Authentication (Priority: P1)

As a security administrator and system operator, I want unauthenticated authentication endpoints (such as login) to enforce strict request limits per IP, so that malicious actors cannot perform automated credential stuffing or brute force attacks against user accounts.

**Why this priority**: Authentication endpoints are the first line of defense. Unrestricted login attempts directly threaten account security and system stability.

**Independent Test**: Send multiple consecutive invalid login requests from a single IP address. Once the threshold is exceeded within the time window, the system must immediately reject additional attempts with HTTP 429 before checking credentials or querying the database.

**Acceptance Scenarios**:

1. **Given** an unauthenticated client making login requests within the quota (e.g., 5 requests per minute), **When** a login request is made, **Then** the request is processed normally and returns appropriate credentials status.
2. **Given** a client that has reached the maximum permitted login attempts within the current window, **When** another login request is sent, **Then** the system returns HTTP 429 Too Many Requests and does not query credentials from the database.

---

### User Story 2 - Protection for Costly AI & Heavy Processing Endpoints (Priority: P1)

As a product manager and cloud infrastructure owner, I want compute-intensive and costly API endpoints (such as interview question generation, interview note aggregation, and audio transcription) to be rate-limited per user/session, so that unintentional abuse or denial-of-service attempts cannot exhaust third-party LLM token budgets or starve server resources.

**Why this priority**: LLM API calls and speech-to-text processing incur financial cost and high compute latency. A burst of requests can exhaust API quotas and disrupt active interview sessions across the entire company.

**Independent Test**: Trigger rapid automated requests to LLM generation or audio processing endpoints as an authenticated user. Verify that excessive calls beyond the threshold are throttled before reaching the LLM service.

**Acceptance Scenarios**:

1. **Given** an authenticated Interviewer or HR personnel requesting question generation within allowed limits (e.g., 20 requests per minute), **When** the request is submitted, **Then** the AI generation pipeline executes and returns results.
2. **Given** a user or client exceeding the allowed AI generation limit, **When** another generation request is dispatched, **Then** the request is blocked with HTTP 429, preventing external LLM API calls.

---

### User Story 3 - Client Rate Limit Visibility & Standardized Feedback (Priority: P2)

As an API client developer or frontend application user, I want clear feedback when a rate limit is approached or reached, including standard headers indicating remaining quota and retry wait time, so that the client application can display helpful UI feedback or throttle itself gracefully.

**Why this priority**: Without informative headers and messages, clients cannot distinguish between transient errors, server failures, and deliberate rate throttling.

**Independent Test**: Inspect response headers of rate-limited endpoints to verify standard rate limit headers (`Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`).

**Acceptance Scenarios**:

1. **Given** any request to a rate-limited endpoint, **When** a response is returned (successful or rejected), **Then** standard response headers convey the limit, remaining quota, and reset timestamp.
2. **Given** a request rejected with HTTP 429, **When** inspected, **Then** the `Retry-After` header indicates the number of seconds the client must wait before retrying, and the response body contains a clear human-readable error message.

---

### User Story 4 - Resilient Fail-Open Behavior (Priority: P3)

As an Interviewer conducting an active interview, I want the system to remain functional even if the rate-limiting infrastructure experiences a transient connection glitch, so that live interview sessions are not terminated or blocked by secondary service issues.

**Why this priority**: Protecting system availability during live interviews is paramount; security mechanisms must not cause collateral downtime if their storage backend temporarily falters.

**Independent Test**: Simulate storage backend disconnect and issue normal API calls. The endpoints should process requests with warning logs rather than crashing or returning 500 errors.

**Acceptance Scenarios**:

1. **Given** the rate limiting cache backend is temporarily unreachable, **When** an interviewer submits notes or requests questions, **Then** the system logs a security warning and allows the request through (fail-open), ensuring uninterrupted user experience.

---

### Edge Cases

- **Reverse Proxy Header Spoofing**: When deployed behind Traefik, client IP must be safely extracted from trusted proxy headers (e.g., leftmost untampered IP in `X-Forwarded-For`), avoiding spoofed headers sent directly by attackers.
- **Concurrent Request Bursts**: Multiple simultaneous requests arriving in parallel within the same millisecond must accurately increment the shared counter without race condition bypasses.
- **Sliding Window Boundaries**: Requests sent right at the boundary between two successive minute windows must not double the permitted volume (sliding window / bucket semantics).
- **Authenticated vs Unauthenticated Mapping**: If an endpoint allows both or is invoked after token validation, authenticated endpoints rate limit by User ID while unauthenticated endpoints rate limit by Client IP.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST identify the request origin accurately: by Client IP for unauthenticated routes, and by Authenticated User ID for authenticated routes.
- **FR-002**: System MUST enforce a strict rate limit on authentication endpoints (`/auth/login`) (default: 5 requests per 60 seconds per IP).
- **FR-003**: System MUST enforce a rate limit on AI generation and resource-heavy endpoints (`/questions/generate`, `/aggregation/generate`, `/transcripts/audio`) (default: 20 requests per 60 seconds per user).
- **FR-004**: System MUST reject requests exceeding the threshold with HTTP status code 429 (Too Many Requests).
- **FR-005**: System MUST include standard rate limit headers in HTTP responses: `Retry-After` (on 429), `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **FR-006**: System MUST maintain state in a distributed cache (Redis) so that rate limits are enforced across horizontal backend replicas behind the reverse proxy.
- **FR-007**: System MUST log rate limiting events (blocked requests) with client IP and endpoint path for security audit trails.
- **FR-008**: System MUST implement a fail-open fallback if the rate limiting store is unreachable, allowing critical user journeys to proceed while recording warnings.

### Key Entities

- **RateLimitPolicy**: Defines rules for endpoints: scope name, threshold (max requests), window duration (seconds), and key extraction strategy (`IP` or `USER`).
- **RateLimitBucket**: Dynamic state stored in cache tracking key identity, current count, and window expiration timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of requests exceeding the designated quota are blocked with HTTP 429 before invoking expensive database or AI logic.
- **SC-002**: Rate limit evaluation overhead per request is under 5ms during normal operations.
- **SC-003**: 0% false-positive rejections for users operating within standard usage quotas.
- **SC-004**: 0% service downtime for legitimate user flows if the rate limiting cache backend temporarily disconnects (fail-open resilience).

## Assumptions

- Traefik reverse proxy forwards legitimate client IP in `X-Forwarded-For` and is configured as a trusted proxy.
- Redis is available as defined in the project stack (`redis:6379`).
- Standard threshold defaults can be overridden via environment variables or central configuration settings.
