# ─────────────────────────────────────────────
# Base Image
# ─────────────────────────────────────────────
# Start from an official Python image.
# "slim" is a minimal variant — it has Python but strips out
# many OS packages that we don't need, keeping the image small.
# Always pin to a specific version (3.11-slim, not just "python")
# so the build is reproducible and won't break on a future update.
FROM python:3.12-slim

# ─────────────────────────────────────────────
# Install Poetry
# ─────────────────────────────────────────────
# Poetry is our dependency manager. We install it via pip.
# Pin the version for the same reason we pin Python:
# a future Poetry release could change behavior and break the build.
RUN pip install poetry==1.8.2

# ─────────────────────────────────────────────
# Working Directory
# ─────────────────────────────────────────────
# Set the working directory inside the container.
# All subsequent commands (COPY, RUN, CMD) will be relative to this path.
# /app is a common convention — it doesn't exist yet, Docker creates it.
WORKDIR /app

# ─────────────────────────────────────────────
# Install Dependencies (with layer caching in mind)
# ─────────────────────────────────────────────
# Copy ONLY the dependency files first, before copying the rest of the code.
#
# Why? Docker builds images layer by layer and caches each layer.
# If we copied all source code first, every code change would invalidate
# the cache and force a full re-run of `poetry install` — which is slow.
# By copying pyproject.toml and poetry.lock first, Docker only re-runs
# `poetry install` when dependencies actually change, not on every code edit.
COPY pyproject.toml poetry.lock ./

# Configure Poetry and install dependencies.
#
# --virtualenvs.create false
#   Normally Poetry creates a virtualenv for isolation.
#   Inside a container, the container itself is already isolated,
#   so a virtualenv inside it is redundant. This disables it.
#
# --only main
#   Only install production dependencies.
#   Dev tools (pytest, ruff, mypy, etc.) are not needed at runtime
#   and would just bloat the image unnecessarily.
#
# --no-interaction --no-ansi
#   Disable prompts and colored output — appropriate for automated builds.
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# ─────────────────────────────────────────────
# Copy Application Source Code
# ─────────────────────────────────────────────
# Now copy the rest of the project into the container.
# This step comes AFTER dependency installation intentionally (see above).
# The first "." is the source (your local project directory).
# The second "." is the destination (WORKDIR, i.e. /app inside the container).
COPY . .

# ─────────────────────────────────────────────
# Expose Port
# ─────────────────────────────────────────────
# Streamlit listens on port 8501 by default.
# EXPOSE documents this for other developers and for Docker networking.
# Note: EXPOSE alone does not publish the port to the host machine —
# that requires -p 8501:8501 when running the container locally.
EXPOSE 8501

# ─────────────────────────────────────────────
# Start Command
# ─────────────────────────────────────────────
# This is the command Docker runs when the container starts.
# We launch Streamlit and explicitly set:
#   --server.port=8501   match the port we declared above
#   --server.address=0.0.0.0   listen on all network interfaces,
#                               not just localhost — required so that
#                               traffic from outside the container can reach it.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
