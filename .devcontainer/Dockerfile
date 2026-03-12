FROM mcr.microsoft.com/devcontainers/base:bookworm

# Install Python
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip zstd && rm -rf /var/lib/apt/lists/*

# Pre-install Ollama binary
RUN curl -fsSL https://ollama.com/install.sh | sh

# Pre-install Python dependencies into a venv
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/py_env \
    && /opt/py_env/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && /opt/py_env/bin/pip uninstall -y nvidia-cublas-cu12 nvidia-cuda-cupti-cu12 nvidia-cuda-nvrtc-cu12 nvidia-cuda-runtime-cu12 nvidia-cufft-cu12 nvidia-cufile-cu12 nvidia-curand-cu12 nvidia-cusparse-cu12 nvidia-cusparselt-cu12 nvidia-nccl-cu12 nvidia-nvshmem-cu12 nvidia-nvtx-cu12 nvidia-nvjitlink-cu12 nvidia-cufile-cu12 nvidia-cusparselt-cu12 2>/dev/null || true \
    && rm /tmp/requirements.txt
