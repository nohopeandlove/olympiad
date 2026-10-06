#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose exec -T backend python -m app.reset_test_limits
(cd backend && ../.venv/bin/pytest -q)
docker compose exec -T backend python -m app.reset_test_limits
(cd frontend && npm run typecheck && npx playwright test)
