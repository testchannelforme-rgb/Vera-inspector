FROM node:24-bookworm
USER root
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /opt/veyra-browser
COPY docker/package*.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
 && npx playwright install --with-deps --no-shell chromium \
 && apt-get update && apt-get install -y --no-install-recommends iptables util-linux \
 && rm -r /var/lib/apt/lists/* \
 && useradd --create-home --uid 1001 pwuser
COPY docker/browser-entrypoint.sh docker/browser-server.cjs docker/probe-network.cjs ./
ENTRYPOINT ["bash","/opt/veyra-browser/browser-entrypoint.sh"]
