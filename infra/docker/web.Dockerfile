FROM node:24-alpine@sha256:a0b9bf06e4e6193cf7a0f58816cc935ff8c2a908f81e6f1a95432d679c54fbfd AS build

WORKDIR /src
COPY packages/render packages/render
RUN cd packages/render && npm ci && npm run build
COPY apps/web apps/web
RUN cd apps/web && npm ci && npm run build

FROM nginx:1.30.3-alpine@sha256:0d3b80406a13a767339fbe2f41406d6c7da727ab89cf8fae399e81f780f814d1

COPY infra/docker/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY infra/docker/validate-web-env.sh /docker-entrypoint.d/05-validate-web-env.sh
RUN chmod +x /docker-entrypoint.d/05-validate-web-env.sh
COPY --from=build /src/apps/web/dist /usr/share/nginx/html
