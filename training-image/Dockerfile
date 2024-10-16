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
    bmon \
    byobu \
    micro \
    git \
    htop \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python3
RUN ln -sf /usr/bin/python3.8 /usr/bin/python3

# Install torch with CUDA support
RUN --mount=type=cache,target=/root/.cache/pip pip install \
   torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html

# Install detectron2 with CUDA support
RUN --mount=type=cache,target=/root/.cache/pip pip install \
   detectron2==0.6 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html

RUN pip install layoutparser[ocr,paddledetection]==0.2.0

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# Run fix scripts
COPY fix-paddleocr.py fix-detectron2.py ./
RUN python3 fix-paddleocr.py
RUN python3 fix-detectron2.py


RUN git clone https://github.com/Layout-Parser/layout-model-training /training
RUN pip install -r /training/requirements.txt pdbpp

COPY ./train_net_patched.py /training/tools/train_net.py
COPY ./base-model/config.yml /training/base-model/config.yml
COPY ./prepare-training.sh /usr/local/bin/prepare-training.sh
