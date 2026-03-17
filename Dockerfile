# Stage 1: Build frontend assets (CSS + HTMX)
FROM node:22-slim AS frontend

WORKDIR /frontend

COPY package.json package-lock.json ./
RUN mkdir -p app/static/js app/static/css
RUN npm ci

COPY postcss.config.mjs ./
COPY app/static/css/input.css app/static/css/input.css
COPY app/templates/ app/templates/

RUN NODE_ENV=production npm run build:css

# Stage 2: Python application
FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

# Copy frontend build artifacts
COPY --from=frontend /frontend/app/static/css/style.css app/static/css/style.css
COPY --from=frontend /frontend/app/static/js/htmx.min.js app/static/js/htmx.min.js

# Run with uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
