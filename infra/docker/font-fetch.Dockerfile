FROM nginx:1.30.3-alpine@sha256:0d3b80406a13a767339fbe2f41406d6c7da727ab89cf8fae399e81f780f814d1

COPY infra/docker/font-fetch-nginx.conf /etc/nginx/nginx.conf
COPY infra/docker/font-fetch.conf /etc/nginx/conf.d/default.conf
