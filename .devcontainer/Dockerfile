# A maintained Node LTS/Debian base with clean distribution APT sources.
# Matching browser binaries and system libraries are baked into the image.
FROM node:24-bookworm
USER root
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /opt/veyra-playwright
COPY docker/package*.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
 && npx playwright install --with-deps --no-shell chromium \
 && apt-get update && apt-get install -y --no-install-recommends python3-venv python3-pip sudo \
 && rm -r /var/lib/apt/lists/*
RUN printf 'node ALL=(root) NOPASSWD:ALL\n' > /etc/sudoers.d/node && chmod 0440 /etc/sudoers.d/node
USER node
