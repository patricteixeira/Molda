FROM node:26-alpine@sha256:e88a35be04478413b7c71c455cd9865de9b9360e1f43456be5951032d7ac1a66 AS build

WORKDIR /src
COPY packages/render packages/render
RUN cd packages/render && npm ci && npm run build
COPY apps/web apps/web
ARG VITE_SYNAPSIS_FONT_BASE_URL=""
ENV VITE_SYNAPSIS_FONT_BASE_URL=${VITE_SYNAPSIS_FONT_BASE_URL}
RUN cd apps/web && npm ci && npm run build

FROM nginx:1.30.3-alpine-slim@sha256:d5b51cfc7d55fc7a7bcf4d1d577b9c3738331df56d68f0b1d8ac9795b9470a5a

COPY infra/docker/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY infra/docker/validate-web-env.sh /docker-entrypoint.d/05-validate-web-env.sh
RUN chmod +x /docker-entrypoint.d/05-validate-web-env.sh
COPY --from=build /src/apps/web/dist /usr/share/nginx/html
