\---

name: project-development

description: Use this skill when developing, reviewing, debugging, testing, refactoring, or designing features for the Interview Assist Agent project. Follow the project's existing architecture and avoid unnecessary changes.

\---



\# Interview Assist Agent - Development Skill



\## General Rules



\- Understand the existing code before modifying it.

\- Do not rewrite entire files when a targeted change is sufficient.

\- Do not modify unrelated files.

\- Preserve the existing architecture unless there is a clear reason to change it.

\- Prefer simple, maintainable solutions over unnecessary abstractions.

\- Before implementing a feature, identify the affected components and data flow.

\- After making changes, verify the affected functionality.



\## Backend



When working on the backend:



\- Follow the existing Spring Boot architecture.

\- Keep Controller responsible for HTTP/API concerns.

\- Keep business logic in Service classes.

\- Keep database access in Repository classes.

\- Use DTOs for API request/response when the project architecture uses DTOs.

\- Prefer constructor injection.

\- Use @Transactional at appropriate service boundaries.

\- Avoid unnecessary database queries.

\- Pay attention to JPA lazy/eager loading and N+1 query problems.

\- Use meaningful exception handling.

\- Do not expose sensitive information in API responses.

\- Preserve existing API contracts unless the task explicitly requires changing them.



\## Database



When modifying database-related code:



\- Inspect existing entities and schema before changing them.

\- Consider indexes for frequently queried columns.

\- Avoid unnecessary joins and repeated queries.

\- Consider transaction boundaries and consistency.

\- Do not change database schema casually.

\- Check whether a migration is required.



\## Frontend



When working on React:



\- Follow the existing component structure.

\- Keep components focused.

\- Reuse existing components and utilities when possible.

\- Avoid unnecessary global state.

\- Handle loading, error, and empty states.

\- Do not introduce a new library when existing dependencies can solve the problem.

\- Keep API communication consistent with the existing project.



\## API



When creating or modifying APIs:



\- Follow REST conventions used by the existing project.

\- Use appropriate HTTP status codes.

\- Validate incoming data.

\- Return consistent response structures.

\- Handle authentication and authorization consistently.

\- Do not expose internal implementation details.



\## Docker



When modifying Docker configuration:



\- Inspect existing Dockerfiles and docker-compose configuration first.

\- Do not expose unnecessary ports.

\- Keep secrets out of Dockerfiles and source code.

\- Prefer environment variables for configuration.

\- Ensure services can communicate using Docker service names rather than hard-coded container IPs.



\## Testing



After implementation:



1\. Run the relevant tests.

2\. Check compilation/build errors.

3\. Check API behavior when applicable.

4\. Check frontend build when frontend code changes.

5\. Report what was tested and any remaining issues.



\## Git



\- Do not create commits unless explicitly requested.

\- Do not reset, revert, or delete user changes without permission.

\- Do not modify unrelated files.

\- Before a potentially destructive operation, explain what will happen and ask for confirmation.



\## Important



When uncertain:



1\. Inspect the existing implementation.

2\. Explain the uncertainty.

3\. Prefer the smallest safe change.

4\. Do not invent project requirements.

