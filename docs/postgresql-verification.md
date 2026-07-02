# PostgreSQL Verification

ApplyFlow keeps SQLite as the default fast local database, but SQLite cannot prove PostgreSQL row
locking, concurrent transactions, partial unique indexes, or cleanup races. This verification track
is a Phase 3 test boundary only. It is not deployment, production infrastructure, cleanup
scheduling, final submission, status lookup, or a production-readiness claim.

## Prerequisites

- Docker Desktop with the Linux engine running, or an equivalent local PostgreSQL server.
- Backend dependencies installed in `backend/.venv`.
- No real credentials or candidate data.

The repository includes a test-only Compose service:

```powershell
docker compose -f docker-compose.postgres-test.yml up -d
docker compose -f docker-compose.postgres-test.yml ps
docker compose -f docker-compose.postgres-test.yml exec postgres-test pg_isready -U applyflow_test -d applyflow_postgres_verification
```

By default, the service binds PostgreSQL to `127.0.0.1:55432` and uses disposable test credentials.
It is not a production database. If the default port is occupied or reserved, choose an unused local
port and set the override before startup:

```powershell
$env:APPLYFLOW_POSTGRES_PORT = "55632"
docker compose -f docker-compose.postgres-test.yml up -d
```

The service remains bound to `127.0.0.1`. Use the same `APPLYFLOW_POSTGRES_PORT` value for startup,
`DATABASE_URL`, test commands, and teardown. The port override is only a local test-service
configuration, not a production database setting. Excluded or occupied port ranges on some machines
can require an override; `55432` is not assumed to fail on every Windows system.

## Environment

Run PostgreSQL checks from `backend/` with explicit test settings:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.postgresql_test_settings"
$env:APPLYFLOW_POSTGRES_TESTS = "1"
$env:APPLYFLOW_POSTGRES_TEST_DATABASE_NAME = "test_applyflow_postgres_verification"
$postgresPort = $env:APPLYFLOW_POSTGRES_PORT
if (-not $postgresPort) { $postgresPort = "55432" }
$env:DATABASE_URL = "postgresql://applyflow_test:applyflow_test_password@127.0.0.1:${postgresPort}/applyflow_postgres_verification"
```

`config.postgresql_test_settings` refuses to load unless the guard is set, the database host is
loopback, the engine is PostgreSQL, and the Django test database name starts with `test_` and differs
from the configured database name.

Direct connectivity proof that Django can use the configured disposable verification base database:

```powershell
.\.venv\Scripts\python.exe -c "import django; django.setup(); from django.db import connection; connection.ensure_connection(); print(connection.vendor); print(connection.connection.info.dbname)"
```

Expected output:

```text
postgresql
applyflow_postgres_verification
```

This command is not a pytest run and does not automatically connect to the pytest-created test
database.

When pytest starts, Django creates or reuses the dedicated disposable test database configured by
`APPLYFLOW_POSTGRES_TEST_DATABASE_NAME`:

```text
test_applyflow_postgres_verification
```

The PostgreSQL test settings require the test database name to start with `test_` and differ from
the base database. The first PostgreSQL test also verifies that the active database name starts with
`test_` and is not `applyflow_postgres_verification`.

## Commands

Focused PostgreSQL concurrency boundary:

```powershell
.\.venv\Scripts\python.exe -m pytest -vv -rs -m postgres tests/test_postgresql_concurrency.py
```

Relevant existing backend coverage on PostgreSQL:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_models.py tests/test_draft_lifecycle.py tests/test_document_models.py tests/test_draft_api.py tests/test_document_api.py tests/test_cleanup_application_drafts.py
```

Full backend suite on PostgreSQL, when practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -vv -rs
```

Ordinary SQLite behavior remains available by clearing the PostgreSQL environment variables and
using `config.settings`. PostgreSQL-only tests skip with an explicit reason when SQLite is selected:

```powershell
Remove-Item Env:\DJANGO_SETTINGS_MODULE -ErrorAction SilentlyContinue
Remove-Item Env:\APPLYFLOW_POSTGRES_TESTS -ErrorAction SilentlyContinue
Remove-Item Env:\APPLYFLOW_POSTGRES_TEST_DATABASE_NAME -ErrorAction SilentlyContinue
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest tests/test_postgresql_concurrency.py
```

## Coverage Boundary

`tests/test_postgresql_concurrency.py` verifies:

- actual PostgreSQL vendor and disposable test database selection;
- simultaneous draft creation with the same creation key;
- draft row locking and stale `If-Match` conflict after lock release;
- simultaneous initial CV uploads;
- simultaneous CV replacements;
- replacement versus deletion;
- replacement versus abandonment;
- partial active-document uniqueness under direct concurrent inserts;
- direct PostgreSQL constraint rejection for the current schema constraints;
- cleanup rechecks for renewed drafts, changed pending-document metadata, hard-delete eligibility,
  orphan references, and overlapping cleanup runs;
- rollback and compensation paths after draft mutation and document metadata failure.

Each concurrent worker opens its own Django database connection and records PostgreSQL backend PIDs.
Race windows use barriers or events, with bounded timeouts. Small bounded waits are used only after
deterministic synchronization to prove a lock is blocking.

The strongest deterministic synchronization currently covers simultaneous draft creation, first
upload, simultaneous replacement, the partial unique constraint, and rollback or constraint cases.
Replacement-versus-delete, replacement-versus-abandonment, and orphan-reference tests verify
important safe outcomes, but they remain partly dependent on scheduler timing or controlled service
seams. This is a test-strength limitation, not a security defect.

The current local verification boundary covers an isolated Docker PostgreSQL test service,
PostgreSQL 17 execution, opt-in PostgreSQL Django settings, matching PostgreSQL and SQLite test
collection, 15 focused PostgreSQL concurrency tests, real independent database connections,
selected row-locking, uniqueness, document lifecycle, cleanup-race, rollback, and compensation
behavior. SQLite remains the default fast local backend.

## Teardown

Remove the test service and disposable database state with:

```powershell
docker compose -f docker-compose.postgres-test.yml down -v
docker compose -f docker-compose.postgres-test.yml ps
```

If `APPLYFLOW_POSTGRES_PORT` was set for startup, leave the same value in the environment for
teardown so Compose resolves the same local service configuration.

## Limitations

Passing these tests proves only the covered PostgreSQL runtime behavior for the current Phase 3
code. It does not prove every possible race, make deadlocks impossible, make local Docker equivalent
to production, or make ApplyFlow production-ready.

Still deferred: production PostgreSQL topology, production credentials, managed database selection,
connection pooling, failover, production load testing, production deadlock retry policy, production
object storage, cleanup scheduling, monitoring and alerting, deployment, backups and restoration,
staff CV download authorization, malware scanning, and Phase 4 final submission/status workflows.
