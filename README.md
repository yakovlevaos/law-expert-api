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

## Continuous deployment

A push to `main` deploys automatically: CI runs lint, types, migrations check
and tests, builds the image, and only then does the `deploy` job SSH into the
server and run `deploy/deploy.sh`. Pull requests never reach the server.

`deploy/deploy.sh` fast-forwards the checkout to `origin/main`, rebuilds the
stack, and waits for `/health/`. If the new revision does not become healthy
within `HEALTH_TIMEOUT` (120s), it resets the checkout back to the previous
commit, rebuilds, and exits non-zero, so a broken release does not stay up.

**Rollback covers code only.** Migrations applied by the entrypoint are not
reverted; a release that changes the schema needs its own rollback plan.

### Repository secrets

| Secret | Value |
| ------ | ----- |
| `DEPLOY_HOST` | Server hostname or IP |
| `DEPLOY_USER` | SSH user, must be in the `docker` group |
| `DEPLOY_PATH` | Absolute path of the checkout on the server |
| `DEPLOY_SSH_KEY` | Private key the runner authenticates with |
| `DEPLOY_KNOWN_HOSTS` | Output of `ssh-keyscan <host>` |
| `DEPLOY_PORT` | Optional, defaults to 22 |

Two different keys are involved, which is easy to mix up:

- the **runner key** (`DEPLOY_SSH_KEY`) — its public half goes into
  `~/.ssh/authorized_keys` of `DEPLOY_USER` on the server;
- a **deploy key on GitHub** — the server runs `git fetch origin` over SSH, so
  it needs its own read-only key registered in the repository's Deploy keys.

```bash
ssh-keygen -t ed25519 -C "github-actions" -f deploy_runner   # -> DEPLOY_SSH_KEY
ssh-keyscan example.com                                      # -> DEPLOY_KNOWN_HOSTS
```

### Server prerequisites

The checkout at `DEPLOY_PATH` must already exist, sit on `main`, and contain a
`.env` (the script refuses to deploy without one, since the container would
not start). `.env` and `volumes/` are gitignored, so neither the reset nor the
rebuild touches secrets, the database or uploaded media. Docker with the
Compose plugin must be installed.

Set the `production` environment in the repository settings to require a
reviewer if the first deploys should be approved by hand.

### Before enabling it

The current `main` predates this branch. Once it is merged, the code requires
PostgreSQL 17 (Django 5.2 refuses to start on 13), and the entrypoint applies
migrations `0002`-`0007`, which rename a table, split titles into their own
model and drop the free-text duration column. Order matters:

1. dump the production database;
2. upgrade the server to `postgres:17-alpine` and restore the dump;
3. merge to `main`;
4. only then let the deploy job run.

Deploying in a different order leaves the container crash-looping on startup.

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
