# --- build stage: resolve dependencies and compile uWSGI -----------------
FROM python:3.12-slim AS builder

# uv is copied in from its own image so the build never depends on pip.
COPY --from=ghcr.io/astral-sh/uv:0.7.5 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    # Build the environment straight at its final path so console-script
    # shebangs stay valid after the copy into the runtime stage.
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml uv.lock ./

# --locked fails the build if uv.lock is stale; --no-default-groups keeps the
# dev group (debug-toolbar, nplusone, ruff, ty) out of the image, and
# --group prod adds uWSGI, which only the image needs.
RUN uv sync --locked --no-default-groups --group prod --no-install-project

# --- runtime stage -------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /server
COPY deploy/uwsgi.ini deploy/entrypoint.sh /deploy/
COPY src/ /server/

RUN chmod +x /deploy/entrypoint.sh && \
    mkdir -p /volumes/data/static /volumes/data/cdn && \
    chown -R app:app /volumes/data /server

USER app

EXPOSE 8099

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8099/health/', timeout=4).status == 200 else 1)"

ENTRYPOINT ["/deploy/entrypoint.sh"]
