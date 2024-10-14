# Stage 1: Build stage
FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04 AS build

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.8 \
    python3.8-dev \
    python3-pip \
    build-essential \
    cmake \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink for python3
RUN ln -sf /usr/bin/python3.8 /usr/bin/python3

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Set the working directory
WORKDIR /app

# Install torch and detectron2 with cache support
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html \
    && pip install detectron2==0.6 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html

# Install Python dependencies (using cache)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Run fix scripts
COPY fix-paddleocr.py fix-detectron2.py ./
RUN python3 fix-paddleocr.py
RUN python3 fix-detectron2.py

# Stage 2: Final runtime stage
FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.8 \
    python3-pip \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python3
RUN ln -sf /usr/bin/python3.8 /usr/bin/python3

# Copy installed dependencies from the build stage
COPY --from=build /usr/local/lib/python3.8 /usr/local/lib/python3.8
COPY --from=build /usr/lib/python3.8 /usr/lib/python3.8
COPY --from=build /root/.cache /root/.cache

# Copy the application
WORKDIR /app
COPY --from=build /app /app

# Set the entrypoint for the application if needed
# ENTRYPOINT ["python3", "your_script.py"]

# Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.8 \
    python3.8-dev \
    python3-pip \
    build-essential \
    cmake \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink for python3
RUN ln -sf /usr/bin/python3.8 /usr/bin/python3

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Set the working directory
WORKDIR /app

# Install torch with CUDA support
RUN pip install --no-cache-dir torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html

# Install detectron2 with CUDA support
RUN pip install --no-cache-dir detectron2==0.6 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html

RUN pip install layoutparser[ocr,paddledetection]==0.2.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run fix scripts
RUN python3 fix-paddleocr.py
RUN python3 fix-detectron2.py
