# syntax=docker/dockerfile:1
# Pipeline image: Python 3.12, Java 17 and the dependencies exactly as locked in uv.lock.
# Data is never copied in (see .dockerignore); docker/run.sh mounts it. Build with
# docker/build.sh, which records the commit the image was built from. Keep the image local:
# never push it.
#
# AI contribution: written with Claude Code (Opus 5.5).

FROM ghcr.io/astral-sh/uv:0.11.16@sha256:440fd6477af86a2f1b38080c539f1672cd22acb1b1a47e321dba5158ab08864d AS uv

# PySpark is locked as a 450 MB source archive. docker/build.sh replaces this empty stage with
# this machine's uv cache entry for it (built from the same locked archive) when one exists;
# otherwise uv downloads the archive. The entry is mounted during the install only, never copied.
FROM scratch AS pyspark-cache

# The image has no .git, so code_state() reports what docker/build.sh records here. A separate
# stage: it runs in parallel with the main one, so a build without these arguments fails within
# seconds, and a new commit does not invalidate the dependency layers below.
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS provenance
ARG GIT_COMMIT
ARG GIT_WORKTREE_CLEAN
RUN if [ -z "$GIT_COMMIT" ] || { [ "$GIT_WORKTREE_CLEAN" != true ] && [ "$GIT_WORKTREE_CLEAN" != false ]; }; then \
        echo "build with docker/build.sh: GIT_COMMIT and GIT_WORKTREE_CLEAN (true or false) are required" >&2; \
        exit 1; \
    fi \
 && printf 'git_commit=%s\ngit_worktree_clean=%s\n' "$GIT_COMMIT" "$GIT_WORKTREE_CLEAN" > /build-provenance.txt

FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

# Spark 4 runs on Java 17. The man directory lets openjdk's install script run on slim images.
RUN mkdir -p /usr/share/man/man1 \
 && apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
 && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /uvx /bin/

WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_CACHE_DIR=/root/.cache/uv

# Dependencies first, so this layer is reused while only the code changes. The uv cache is a
# build cache mount: downloads survive a failed build and never end up in the image. The
# sdists-v9 path matches uv 0.11's cache layout; with another uv version the mount is unused.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,from=pyspark-cache,target=/root/.cache/uv/sdists-v9/pypi/pyspark,rw \
    uv sync --frozen --no-install-project --group measure

# The project, installed editable: etf_risk stays at /app/src/etf_risk, so provenance.resolve()
# finds the repository root (/app) for the data paths stored in configs.
COPY src/ src/
COPY tests/ tests/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group measure

# Runs as a non-root user; it owns /app (for pytest's cache) but not the installed code.
RUN useradd --create-home --uid 1000 app && chown app /app

# Provenance, checked in its own stage above; declared last so that only these steps change
# with each commit.
COPY --from=provenance /build-provenance.txt /usr/local/share/etf-risk/build-provenance.txt
ARG GIT_COMMIT
ARG GIT_WORKTREE_CLEAN
ENV PATH=/app/.venv/bin:$PATH \
    ETF_RISK_GIT_COMMIT=$GIT_COMMIT \
    ETF_RISK_GIT_WORKTREE_CLEAN=$GIT_WORKTREE_CLEAN
LABEL org.opencontainers.image.title="etf-risk pipeline" \
      org.opencontainers.image.revision=$GIT_COMMIT

USER app
CMD ["pytest"]
