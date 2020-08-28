# Stage 1 -- create a python3.8 builder image
FROM python:3.8-slim-buster AS pre-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    default-mysql-client \
    python3-dev \
    libffi-dev \
    libssl-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Stage 2 -- perform app specific build tasks
FROM pre-builder AS builder

WORKDIR /opt/CTFd

RUN mkdir -p /opt/CTFd

ENV PATH=/root/.local/bin:$PATH

COPY . /opt/CTFd

RUN pip install --user -r requirements.txt --no-cache-dir
RUN for d in CTFd/plugins/*; do \
    if [ -f "$d/requirements.txt" ]; then \
    pip install --user -r $d/requirements.txt --no-cache-dir; \
    fi; \
    done; \
    mv /root/.local /opt/CTFd/.local

# Stage 3 -- create final app image
FROM python:3.8-slim-buster

WORKDIR /opt/CTFd

RUN mkdir -p /var/log/CTFd /var/uploads

COPY --from=builder /opt/CTFd /opt/CTFd

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    default-mysql-client \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN adduser \
    --home /opt/CTFd \
    --no-create-home \
    --disabled-login \
    --uid 1001 \
    --gecos "" \
    --shell /bin/bash \
    ctfd

RUN chmod +x /opt/CTFd/docker-entrypoint.sh \
    && chown -R 1001:1001 /opt/CTFd /var/log/CTFd /var/uploads

ENV PATH=/opt/CTFd/.local/bin:$PATH

USER 1001
EXPOSE 8000
ENTRYPOINT ["/opt/CTFd/docker-entrypoint.sh"]