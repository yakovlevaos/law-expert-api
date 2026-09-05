# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Genesis is a Django REST Framework backend API server for a games catalog. It's a read-only API that provides information about video games, including metadata like genres, platforms, modes, competencies, duration, and authors.

## Development Commands

### Setup
```bash
# Install dependencies using uv (creates .venv from uv.lock)
make deps

# Start development database only
make up_db

# Run development server (requires database to be running)
make dev
```

### Database Management
```bash
# Create and apply migrations
make migrate

# Database backup
make dump

# Database restore
make restore
```

### Docker Commands
```bash
# Start full production stack (database + API server)
make up

# Stop all services
make down
```

## Project Architecture

### Technology Stack
- **Framework**: Django 5.2 with Django REST Framework
- **Database**: PostgreSQL 17 (managed via docker-compose)
- **WSGI Server**: uWSGI (production)
- **API Documentation**: drf-spectacular (Swagger UI available in debug mode)
- **Dependency Management**: uv (PEP 621 `[project]` + PEP 735 `[dependency-groups]`, `uv.lock` is committed)
- **Lint / format**: ruff · **Types**: ty
- **Python Version**: 3.12

### Directory Structure

```
genesis/
├── src/                      # Main application code
│   ├── apps/                 # Django applications
│   │   └── games/           # Games catalog app
│   │       ├── models.py    # Game, Genre, Mode, Platform, etc.
│   │       ├── serializers.py
│   │       ├── filters.py   # django-filter FilterSet for games
│   │       ├── durations.py # Playtime parsing / formatting
│   │       ├── views.py     # Read-only ViewSets
│   │       ├── urls.py      # API routing
│   │       └── tests/       # Test suite
│   ├── config/              # Django project settings
│   │   ├── settings.py      # Main settings file
│   │   ├── urls.py          # Root URL configuration
│   │   ├── pagination.py    # Project-wide pagination defaults
│   │   ├── views.py         # /health/ probe
│   │   └── wsgi.py
│   ├── helpers/             # Utility scripts
│   │   └── fill_db.py       # Database seeding script
│   └── manage.py
├── deploy/                  # Deployment configurations
├── volumes/                 # Docker volumes (data, media, static)
└── docker-compose.yaml
```

### Core Application: Games

The `apps.games` application is the primary feature, implementing a games catalog with the following models:

**Main Models:**
- `Game`: Central model with title, description, cover image, playtime range, and relationships to other entities
- `AlternativeTitle`: Extra names a game ships under (FK to Game, `related_name="alternative_titles"`)
- `Author`: Game creators/developers
- `Genre`: Game genres (e.g., "Hack and slash", "Приключенческий боевик")
- `Mode`: Game modes (e.g., "Одиночный")
- `Platform`: Gaming platforms (e.g., "PS4", "PS5", "ПК")
- `Competency`: Educational/developmental competencies
- `Duration`: Duration categories
- `ScreenShot`: Related screenshots for games

**Key Model Relationships:**
- Game has ForeignKey to Author and Duration
- Game has ManyToMany relationships with Genre, Competency, Platform, and Mode
- ScreenShot has ForeignKey to Game (related_name="screen_shots")

### API Endpoints

All endpoints are read-only (GET, HEAD) and located under `/api/v1/`:

- `/api/v1/games/` - Games list with pagination (30 per page)
- `/api/v1/genres/` - Available genres
- `/api/v1/modes/` - Game modes
- `/api/v1/platforms/` - Gaming platforms
- `/api/v1/competencies/` - Competencies
- `/api/v1/durations/` - Duration types
- `/api/v1/authors/` - Game authors

**Debug-only endpoints:**
- `/api/v1/docs/` - Swagger UI documentation
- `/api/v1/schema/` - OpenAPI schema
- `/admin/` - Django admin interface

### Important Implementation Details

**Custom Ordering in GameViewSet:**
The Games queryset uses custom ordering logic in `src/apps/games/views.py` that handles titles starting with "Серия игр " specially - it sorts them by the substring after that prefix rather than the full title. `id` is always the final ordering key so that pagination stays deterministic.

**Titles and playtime:**
A game has one primary `title` plus `AlternativeTitle` rows; the API returns them together as `titles_list`. Playtime lives in `duration_hours_min`/`duration_hours_max` (both NULL means endless), and the `duration` string in the response is generated from that range by `src/apps/games/durations.py` - do not reintroduce a free-text duration field.

**Query Optimization:**
The GameViewSet uses `select_related()` for foreign keys (author, duration_type) and `prefetch_related()` for many-to-many relationships to avoid N+1 queries.

**Debug Tools:**
- django-debug-toolbar: Available when DEBUG=True
- nplusone: Detects N+1 query issues (configured to WARN level)

### Environment Configuration

The application uses `django-environ` for environment configuration. Required environment variables (see `.env.example`):

- `SECRET_KEY`: Required when `DEBUG=false`
- `ALLOWED_HOSTS`: Required when `DEBUG=false`, comma separated
- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password
- `DATABASE_URL`: Full database connection string (format: `psql://user:password@host:port/dbname`)
- `DEBUG`: Enable/disable debug mode (true/false)
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `ANON_THROTTLE_RATE`, `API_CACHE_SECONDS`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`

### Development vs Production

**Development mode** (DEBUG=True):
- Uses `python src/manage.py runserver`
- Debug toolbar and nplusone middleware enabled
- API documentation endpoints available
- Media files served directly by Django

**Production mode:**
- Runs in Docker with uWSGI (3 processes, 20s harakiri, 5000 max requests)
- Automatic migrations and static file collection on startup
- Serves on port 8099
- Static and media files served from `/volumes/data/`

### Database Seeding

The `src/helpers/fill_db.py` script contains raw game data in Russian for seeding the database with initial content. This is used to populate the games catalog.

### Testing Notes

- Tests live in `src/apps/games/tests/`; `factories.py` builds games with their required relations
- Run tests with `make test` (or `uv run python src/manage.py test apps`)
- `make lint` runs ruff (format + check) and ty; `make fmt` auto-fixes; `make types` is ty alone
- `make check_deploy` runs Django's deployment checklist
- Always run commands through `uv run`, never a bare `python`

### Common Gotchas

- All Django management commands must be run through `uv run python src/manage.py`
- Dependencies are edited with `uv add` / `uv add --group dev`, never by hand-editing the lockfile; run `uv lock` after changing `pyproject.toml`
- ty passes only because the dev group pins `django-types` and `djangorestframework-types`; reverse relations, implicit `<fk>_id` columns and the DRF mixin base are declared under `if TYPE_CHECKING`
- Language code is set to "ru-RU" - model verbose names and some content are in Russian
- CORS origins come from `CORS_ALLOWED_ORIGINS`; every origin is allowed only when `DEBUG` is on and that list is empty
- `SECRET_KEY` and `ALLOWED_HOSTS` are required when `DEBUG=false`; the app refuses to start without them
- `debug_toolbar` and `nplusone` are dev-only dependencies - never import them at module level
