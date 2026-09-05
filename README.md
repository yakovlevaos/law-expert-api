# Genesis

Read-only REST API for a video games catalog: games with their genres,
platforms, modes, competencies, duration and authors.

Django 5.2 · Django REST Framework · PostgreSQL 17 · uWSGI · Python 3.12

Tooling is the Astral stack: [uv](https://docs.astral.sh/uv/) for dependencies,
[ruff](https://docs.astral.sh/ruff/) for linting and formatting, and
[ty](https://docs.astral.sh/ty/) for type checking.

## Quick start

```bash
cp .env.example .env
# generate a secret key and paste it into .env
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"

make deps      # uv sync: create .venv and install everything
make up_db     # start the development database
make migrate   # apply migrations
make dev       # http://127.0.0.1:8000
```

Seed the catalog with the bundled sample data:

```bash
uv run python src/helpers/fill_db.py
```

## Common commands

| Command             | What it does                              |
| ------------------- | ----------------------------------------- |
| `make help`         | List every target                         |
| `make deps`         | `uv sync` -- install everything            |
| `make lock`         | Refresh `uv.lock`                         |
| `make dev`          | Run the development server                |
| `make test`         | Run the test suite                        |
| `make lint`         | Ruff format check + lint + ty             |
| `make types`        | Type-check with ty                        |
| `make fmt`          | Auto-format and auto-fix                  |
| `make check_deploy` | Django production readiness checklist     |
| `make up` / `down`  | Start / stop the full Docker stack        |
| `make dump`         | Dump the database into `volumes/`         |
| `make restore`      | Restore the database from a dump          |

Management commands need `src/manage.py`, not `manage.py`:

```bash
uv run python src/manage.py createsuperuser
```

## API

Everything lives under `/api/v1/` and answers to `GET` and `HEAD` only.

| Endpoint             | Description       |
| -------------------- | ----------------- |
| `/api/v1/games/`     | Games catalog     |
| `/api/v1/genres/`    | Genres            |
| `/api/v1/modes/`     | Game modes        |
| `/api/v1/platforms/` | Platforms         |
| `/api/v1/competencies/` | Competencies   |
| `/api/v1/durations/` | Duration types    |
| `/api/v1/authors/`   | Authors           |

Every list endpoint is paginated (`?page=`, `?page_size=`, 30 by default,
200 max) and responses carry `Cache-Control` and an `ETag` for revalidation.

`/health/` reports database connectivity for probes. With `DEBUG=true` the
Swagger UI is at `/api/v1/docs/`, the schema at `/api/v1/schema/`, and the
Django admin at `/admin/`.

### Filtering games

```
GET /api/v1/games/?genres=3&genres=7      # any of these genres (repeatable)
GET /api/v1/games/?genre=Песочница        # by name, case-insensitive
GET /api/v1/games/?platforms=1&modes=2
GET /api/v1/games/?duration_type=4&author=2
GET /api/v1/games/?duration_min=20        # at least 20 hours
GET /api/v1/games/?duration_max=5         # at most 5 hours
GET /api/v1/games/?endless=true           # games with no fixed playtime (∞)
GET /api/v1/games/?search=человек-паук    # title, alternative titles, description
GET /api/v1/games/?ordering=duration_hours_min   # title, created_at, duration_hours_min
```

`genre`, `platform`, `mode` and `competency` are the name-based singular
variants of the id-based plural filters.

Without `ordering`, games are sorted by title with one exception: a title
starting with `Серия игр ` sorts under the series name that follows the
prefix, so `Серия игр Devil May Cry 1-5` lands under `D`, not `С`.

## Configuration

Configuration comes from the environment (see `.env.example`).

| Variable                | Notes                                                    |
| ----------------------- | -------------------------------------------------------- |
| `SECRET_KEY`            | **Required** when `DEBUG=false`                           |
| `DEBUG`                 | `false` by default                                        |
| `ALLOWED_HOSTS`         | **Required** when `DEBUG=false`, comma separated          |
| `DATABASE_URL`          | `psql://user:password@host:port/dbname`                   |
| `CORS_ALLOWED_ORIGINS`  | Comma separated; empty + `DEBUG` allows every origin      |
| `CSRF_TRUSTED_ORIGINS`  | Comma separated                                           |
| `ANON_THROTTLE_RATE`    | Anonymous rate limit, `120/min` by default                |
| `API_CACHE_SECONDS`     | `Cache-Control: max-age`, `300` by default; `0` disables  |
| `SECURE_SSL_REDIRECT`   | Enable behind a TLS-terminating proxy                     |
| `SECURE_HSTS_SECONDS`   | `0` disables HSTS                                         |

`debug_toolbar` and `nplusone` are development-only dependencies and are not
installed in the production image.

## Production

```bash
make up
```

The image builds with `uv sync --locked --no-default-groups --group prod`, so
the dev group (debug-toolbar, nplusone, ruff, ty) never reaches production and
a stale `uv.lock` fails the build. uWSGI sits in its own `prod` group because
it has no wheels and compiling it on CI is slow and fragile -- only the image
installs it. It copies `src/` in, runs as a non-root user, and
starts uWSGI via `deploy/entrypoint.sh`, which applies migrations and collects
static files. uWSGI serves `/static/` and `/cdn/` from `/volumes/data` (see
`deploy/uwsgi.ini`). The API listens on port 8099.

### uWSGI workers

`deploy/uwsgi.ini` runs **3 worker processes** plus a master that supervises
them and serves nothing itself. There are no threads, so a worker handles one
request at a time and the server answers 3 concurrent requests.

| Setting | Value | Meaning |
| ------- | ----- | ------- |
| `processes` | 3 | Worker processes |
| `harakiri` | 20 | A request running longer than 20s kills its worker |
| `max-requests` | 5000 | A worker respawns after 5000 requests, capping leaks |

Measured on the seeded catalog: the whole catalog (`?page_size=200`) takes
~118 ms and a default page of 30 games ~41 ms, which puts the ceiling at
roughly 25 and 70 requests per second respectively.

Raise `processes` only when the CPU is genuinely the bottleneck --
`2 x $(nproc) + 1` is the usual starting point. Note that ~90% of that 118 ms
is Python re-serialising the same rows, so caching the response buys far more
than extra workers.

## Continuous deployment

A push to `main` deploys automatically. Pull requests run the checks but never
reach the server.

What a push to `main` triggers, in order:

1. **`test`** -- `ruff format --check`, `ruff check`, `ty check`, a
   missing-migration check, Django's deployment checklist, and the test suite
   against PostgreSQL 17.
2. **`docker`** -- builds the production image, so a broken Dockerfile is
   caught before the server is touched.
3. **`deploy`** -- runs only if both succeeded. It writes `DEPLOY_SSH_KEY` to
   the runner, SSHes in as `DEPLOY_USER@DEPLOY_HOST`, and runs
   `deploy/deploy.sh` in `DEPLOY_PATH`.

The job belongs to the `production` environment (add a required reviewer there
to gate deploys) and to a non-cancelling concurrency group, so two pushes queue
instead of racing and an older commit cannot overtake a newer one.

On the server, `deploy/deploy.sh`:

1. refuses to run if `.env` is missing -- the container would not start;
2. `git fetch --prune origin main`, then `git checkout -B main origin/main`
   (a plain `reset --hard` would move whichever branch is checked out and
   leave the server on a stale branch name);
3. `docker compose --profile prod up -d --build`, which runs
   `deploy/entrypoint.sh`: migrations, `collectstatic`, then uWSGI;
4. polls `/health/` for up to `HEALTH_TIMEOUT` (120s);
5. on failure, dumps the container logs, resets to the previous commit,
   rebuilds, and exits non-zero.

If the target commit is already checked out it only makes sure the stack is
up, so re-running a deploy is harmless.

**Rollback covers code only.** Migrations applied by the entrypoint are not
reverted; a release that changes the schema needs its own rollback plan --
take a database dump first, and be ready to restore it.

Watch a deploy, or re-run one after fixing a secret, with:

```bash
gh run watch <run-id> --repo <owner>/<repo>
```

### Repository secrets

| Secret | Value |
| ------ | ----- |
| `DEPLOY_HOST` | Server hostname or IP |
| `DEPLOY_USER` | SSH user, must be in the `docker` group |
| `DEPLOY_PATH` | Absolute path of the checkout on the server |
| `DEPLOY_SSH_KEY` | Private key the runner authenticates with |
| `DEPLOY_KNOWN_HOSTS` | Output of `ssh-keyscan <host>` |
| `DEPLOY_PORT` | Optional, defaults to 22 |

`DEPLOY_SSH_KEY` is the **private** half of a dedicated key pair; its public
half goes into `~/.ssh/authorized_keys` of `DEPLOY_USER` on the server. Give it
no passphrase -- the runner connects with `BatchMode=yes` and cannot answer a
prompt.

```bash
ssh-keygen -t ed25519 -C "github-actions" -f deploy_runner -N ''
gh secret set DEPLOY_SSH_KEY < deploy_runner    # never paste it by hand
ssh-copy-id -i deploy_runner.pub user@example.com
ssh-keyscan -H example.com | gh secret set DEPLOY_KNOWN_HOSTS
```

Set the secret from the file rather than the clipboard: a key whose line breaks
were lost fails on the runner with `Load key: error in libcrypto`, before it
ever reaches the server.

While the repository is public the server fetches over HTTPS and needs no
credentials of its own. If it ever becomes private, give the server its own
read-only key and register it under the repository's Deploy keys.

### Server prerequisites

The checkout at `DEPLOY_PATH` must already exist, sit on `main`, and contain a
`.env` (the script refuses to deploy without one, since the container would
not start). `.env` and `volumes/` are gitignored, so neither the reset nor the
rebuild touches secrets, the database or uploaded media. Docker with the
Compose plugin must be installed.

Set the `production` environment in the repository settings to require a
reviewer if the first deploys should be approved by hand.

### Releases that change the schema

The entrypoint migrates on every start, so a schema change ships with the
deploy and the automatic rollback cannot undo it. Before merging one:

1. dump the database (`make dump`), and verify the dump is complete --
   `tail -5` must contain `PostgreSQL database dump complete`;
2. rehearse the migration on a scratch copy of that dump;
3. merge, and keep the dump until the release has settled.

The same applies to a PostgreSQL major upgrade: dump, move the old data
directory aside rather than deleting it, start the new version, restore, and
only then let the application start.

## Type checking

`make types` runs ty over `src/`. Django's ORM is heavily dynamic, so the dev
group pins `django-types` and `djangorestframework-types` -- stub packages that
work without a mypy plugin, which is what makes `Model.objects` and field
descriptors resolve correctly for ty.

Two things stubs cannot express are declared in the code instead: reverse
relation accessors and the implicit `<fk>_id` columns are declared under
`if TYPE_CHECKING` in `models.py`, and `CacheControlMixin` gets an `APIView`
base under `TYPE_CHECKING` (a plain `object` at runtime) so its `super()` calls
resolve.

## Layout

```
src/
  apps/games/        catalog app: models, serializers, filters, views, tests
  config/            settings, root urls, pagination, health check
  helpers/fill_db.py sample data seeding script
deploy/              uWSGI config, entrypoint, Postgres init
volumes/             Docker volumes: database, static and media files
pyproject.toml       Dependencies (PEP 621 + PEP 735) and tool config
uv.lock              Resolved dependency lockfile -- commit it
```

## Titles and playtime

A game has one primary `title` plus any number of `AlternativeTitle` rows for
the other names it ships under (`God of War` / `God of War: Ragnarok`). The API
exposes them together as `titles_list`, primary name first. Ordering,
uniqueness and the `Серия игр` rule all operate on the primary title.

Playtime is stored as an hour range, `duration_hours_min` / `duration_hours_max`
(both `NULL` means endless -- the `duration_type` reference says "бесконечная").
The `duration` string in the response is generated from that range, so there is
a single source of truth: `(10, 10)` renders as `10 часов`, `(5, 10)` as
`5-10 часов`, `(None, None)` as `∞`.

Migrations `0004`-`0006` move the old data across and are fully reversible.
They are split in three because Postgres refuses to `ALTER` a table that has
pending trigger events from row updates in the same transaction.
