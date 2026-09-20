# Implementation Plan: Sensitive API Rate Limiting

**Branch**: `001-rate-limiting` | **Date**: 2026-09-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-rate-limiting/spec.md`

## Summary

Implement distributed, Redis-backed rate limiting for sensitive endpoints across horizontally scaled FastAPI backend replicas. Focuses on protecting authentication (`/auth/login` - 5/min by IP) against credential stuffing and costly AI/heavy processing routes (`/questions/generate`, `/aggregation/generate`, `/transcripts/audio` - 20/min by User ID) against DoS and token budget exhaustion. Returns standard HTTP 429 and `Retry-After` headers, with fail-open resilience when Redis is unavailable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI (>=0.110), Redis (>=5.0), Pydantic v2 (Settings & Schemas)  
**Storage**: Redis 7 (distributed sliding/fixed window counters with TTL)  
**Testing**: pytest, pytest-asyncio, httpx TestClient  
**Target Platform**: Linux container (Docker Compose with 3 scaled backend replicas behind Traefik v3)  
**Project Type**: Web Service API (FastAPI Backend)  
**Performance Goals**: Rate-limiting inspection overhead < 2ms per request  
**Constraints**: Zero memory leak; backend must remain strictly stateless; fail-open on transient Redis failure; Traefik `X-Forwarded-For` support  
**Scale/Scope**: 3 backend replicas sharing single Redis cluster/instance; up to 100 concurrent interview sessions  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **HITL Enforcement**: Rate limiting does not alter or automate council hiring decisions. (PASS)
- [x] **Privacy & Anonymity**: Rate limiting identifiers use hashed/raw IPs and user IDs; no interview notes or private council evaluation data are logged or exposed. (PASS)
- [x] **Compliance & Filtering**: Rate limiting operates before LLM pipelines, adding defensive protection to the AI endpoints. (PASS)
- [x] **Stateless Backend**: Rate limits are stored strictly in Redis (`redis:6379`), ensuring complete statelessness and multi-replica horizontal scaling. (PASS)
- [x] **Security & Cyber Defense**: Directly implements Section V (Security: Rate-limiting on sensitive endpoints) and prevents DoS / Brute-force. (PASS)
- [x] **Quality Gates**: Requires 100% pass on `ruff check` and `pytest tests/test_rate_limit.py`. (PASS)

## Project Structure

### Documentation (this feature)

```text
specs/001-rate-limiting/
├── plan.md              # This implementation plan
├── research.md          # Architecture decisions & Redis strategy
├── data-model.md        # Redis key format & header specifications
├── quickstart.md        # Verification and curl test guide
├── contracts/           # API response schemas (429 Too Many Requests)
└── tasks.md             # Implementation tasks
```

### Source Code (affected areas)

```text
backend/
├── app/
│   ├── core/
│   │   ├── config.py         # Rate limit settings (defaults, enabled flag)
│   │   └── rate_limit.py     # RateLimiter dependency & Redis atomic counter
│   ├── api/
│   │   ├── auth.py           # Apply RateLimiter on /auth/login (5/min)
│   │   ├── questions.py      # Apply RateLimiter on /questions/generate (20/min)
│   │   ├── aggregation.py    # Apply RateLimiter on /aggregation/generate (20/min)
│   │   └── transcripts.py    # Apply RateLimiter on /transcripts/audio (20/min)
└── tests/
    └── test_rate_limit.py    # Unit & integration tests for rate limiting & fail-open
```

**Structure Decision**: Add `RateLimiter` class in `app/core/rate_limit.py` as a reusable FastAPI dependency, cleanly configurable via `app/core/config.py`. Apply to sensitive router endpoints via `Depends(RateLimiter(...))`.

## Complexity Tracking

*No constitutional violations. Zero unnecessary abstractions.*
