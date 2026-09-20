# Tasks: Sensitive API Rate Limiting

**Feature Branch**: `001-rate-limiting`  
**Input**: [plan.md](./plan.md) and [spec.md](./spec.md)

## Phase 1: Setup & Configuration

- [x] T001 Add rate limiting settings (`rate_limit_enabled`, `rate_limit_login_per_minute`, `rate_limit_ai_per_minute`) to `backend/app/core/config.py`.

---

## Phase 2: Foundational Infrastructure (Blocking Prerequisites)

- [x] T002 Implement `RateLimiter` dependency in `backend/app/core/rate_limit.py` supporting:
  - Client IP extraction (Traefik `X-Forwarded-For` support).
  - User ID extraction from authentication context.
  - Redis atomic counter (`INCR` + `EXPIRE`).
  - Rate limit headers calculation (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`).
  - Fail-open fallback when Redis is unreachable.

---

## Phase 3: User Story 1 (P1) - Authentication Endpoint Protection (Login)

- [x] T003 [US1] Write test in `backend/tests/test_rate_limit.py` for `/api/auth/login` rate limiting (exceeding limit triggers HTTP 429).
- [x] T004 [US1] Apply `RateLimiter` dependency to `/api/auth/login` route in `backend/app/api/auth.py`.

---

## Phase 4: User Story 2 (P1) - AI & Heavy Processing Endpoint Protection

- [x] T005 [US2] Write test in `backend/tests/test_rate_limit.py` for AI endpoints (`/api/questions/generate`, `/api/aggregation/generate`) rate limiting by User ID.
- [x] T006 [US2] Apply `RateLimiter` dependency to question generation endpoint in `backend/app/api/questions.py`.
- [x] T007 [US2] Apply `RateLimiter` dependency to aggregation endpoint in `backend/app/api/aggregation.py`.
- [x] T008 [US2] Apply `RateLimiter` dependency to audio transcription endpoint in `backend/app/api/transcripts.py`.

---

## Phase 5: User Story 3 & 4 (P2 & P3) - Headers & Fail-Open Resilience

- [x] T009 [US3] Write test verifying `X-RateLimit-*` and `Retry-After` response headers on allowed and rejected requests.
- [x] T010 [US4] Write test in `backend/tests/test_rate_limit.py` simulating Redis failure and ensuring requests fail-open smoothly.

---

## Phase 6: Polish & Quality Gates

- [x] T011 Run `ruff check backend` and ensure zero lint warnings.
- [x] T012 Run `pytest backend/tests/` and ensure 100% passing tests.
