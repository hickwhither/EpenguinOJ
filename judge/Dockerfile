FROM python:3.12-slim

ENV TZ=UTC
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata g++ make libcap-dev pkg-config ca-certificates git curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && git clone --depth 1 https://github.com/ioi/isolate.git /tmp/isolate \
    && make -C /tmp/isolate isolate install \
    && rm -rf /tmp/isolate /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . ./

ENTRYPOINT ["python", "main.py"]
