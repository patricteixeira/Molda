FROM node:26-alpine@sha256:e88a35be04478413b7c71c455cd9865de9b9360e1f43456be5951032d7ac1a66 AS render

WORKDIR /src
COPY packages/render packages/render
RUN cd packages/render && npm ci && npm run build

FROM mcr.microsoft.com/playwright/python:v1.61.0-noble@sha256:a9731514f24121d1dcd25d58d0a38146646d290a5998fd80d3e533e7b5e21c69

WORKDIR /app
COPY packages/engine packages/engine
COPY apps/api apps/api
RUN python -m pip install --no-cache-dir --upgrade pip==26.1.2 \
    && python -m pip install --no-cache-dir \
      -r packages/engine/requirements-lock.txt \
      -r apps/api/requirements-lock.txt \
    && python -m pip install --no-cache-dir --no-deps -e packages/engine -e apps/api \
    && python -m pip check
COPY --from=render /src/packages/render/dist /app/render-dist
RUN groupadd --system --gid 10001 brandrt \
    && useradd --system --uid 10001 --gid brandrt --home-dir /tmp --shell /usr/sbin/nologin brandrt \
    && mkdir -p /data \
    && chown -R brandrt:brandrt /app /data

ENV BRANDRT_RENDER_DIST=/app/render-dist
ENV BRANDRT_DATA_DIR=/data
ENV HOME=/tmp
ENV PYTHONDONTWRITEBYTECODE=1

USER brandrt

CMD ["brand-api", "worker"]
