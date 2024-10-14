# Use NVIDIA's CUDA base image with Python 3.9
FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.9 \
    python3.9-dev \
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
RUN ln -s /usr/bin/python3.9 /usr/bin/python3

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Set the working directory
WORKDIR /app

# Install torch with CUDA support
RUN pip install --no-cache-dir torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html

# Install detectron2 with CUDA support
RUN pip install --no-cache-dir detectron2==0.6 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run fix scripts
RUN python3 fix-paddleocr.py
RUN python3 fix-detectron2.py
