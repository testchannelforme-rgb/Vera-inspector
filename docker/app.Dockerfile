FROM node:24-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build && npm prune --omit=dev --no-audit --no-fund
FROM python:3.12-slim-bookworm
WORKDIR /opt/veyra
COPY backend/requirements* backend/constraints.txt ./backend/
RUN python -m pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY scripts/compile-studio.mjs ./scripts/compile-studio.mjs
ARG VEYRA_REVISION=unknown
RUN printf "%s" "$VEYRA_REVISION" > BUILD_REVISION
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
COPY --from=frontend /build/frontend/node_modules ./frontend/node_modules
COPY --from=frontend /build/frontend/package.json ./frontend/package.json
COPY docker/gateway.py ./docker/gateway.py
COPY --from=frontend /build/frontend/dist ./frontend/dist
ENV PYTHONPATH=/opt/veyra/backend PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 veyra && mkdir -p /opt/veyra/.veyra-runtime && chown veyra:veyra /opt/veyra/.veyra-runtime
USER veyra
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1","--no-proxy-headers","--no-access-log","--limit-concurrency","24"]
