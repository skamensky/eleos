.PHONY: supabase-up supabase-down supabase-e2e openapi web-types

supabase-up:
	docker compose \
		-f test_env/supabase/docker-compose.yml \
		-f test_env/supabase/docker-compose.eleos.yml \
		up -d --build

supabase-down:
	docker compose \
		-f test_env/supabase/docker-compose.yml \
		-f test_env/supabase/docker-compose.eleos.yml \
		down -v

supabase-e2e:
	uv run python scripts/e2e/run_supabase_e2e.py

openapi:
	uv run python scripts/generate_openapi.py --output docs/eleos-openapi.json

web-types:
	cd web && npm run generate:types
