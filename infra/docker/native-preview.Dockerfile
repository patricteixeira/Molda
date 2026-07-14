FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        fontconfig \
        fonts-liberation2 \
        libreoffice-impress \
        libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

COPY packages/engine packages/engine
RUN python -m pip install --no-cache-dir --upgrade pip==26.1.2 \
    && python -m pip install --no-cache-dir -r packages/engine/requirements-lock.txt \
    && python -m pip install --no-cache-dir --no-deps -e packages/engine \
    && python -m pip check \
    && groupadd --system --gid 10002 preview \
    && useradd --system --uid 10002 --gid preview --home-dir /work --shell /usr/sbin/nologin preview \
    && mkdir -p /work \
    && chown preview:preview /work

ENV HOME=/work
ENV PYTHONDONTWRITEBYTECODE=1

USER preview

ENTRYPOINT ["brandrt"]
CMD ["--help"]
