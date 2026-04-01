FROM mcr.microsoft.com/devcontainers/base:bookworm

# Install prerequisites
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        zstd curl ca-certificates python3 python3-venv python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Pre-build the Python virtual environment
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/py_env && \
    /opt/py_env/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Install Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Pre-install Ollama (binary only — no model pull)
RUN curl -fsSL https://ollama.com/install.sh | sh

