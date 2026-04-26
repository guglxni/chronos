# ── Build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# VITE_API_URL must be supplied as a build-arg because Vite bakes it into the
# static bundle at compile time — a runtime environment variable has no effect
# on already-compiled JS.  Default targets the host-published API port so
# `docker compose up` works without extra configuration.
ARG VITE_API_URL=http://localhost:8100
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json .
RUN npm ci --prefer-offline
COPY . .
RUN npm run build

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:3000/ > /dev/null || exit 1
