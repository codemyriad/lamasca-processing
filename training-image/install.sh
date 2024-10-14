#!/bin/sh

# Install layoutparser, paddleocr, torch and detectron2 v0.6

set -e

install_pip() {
    curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py
}

install_detectron2() {
    #python3 -m pip install -U 'git+https://github.com/facebookresearch/detectron2.git@ebe8b45437f86395352ab13402ba45b75b4d1ddb'

    pip3 install detectron2==0.6 -f \
    https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html
}
install_torch() {
    echo "Installing torch"
    pip3 install torch==1.10 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
}

# This will install layoutparser and paddleocr with CPU support
python3 -m pip > /dev/null || install_pip
pip show Pillow || pip install pillow==9.5.0
pip show torchvision | egrep 'Name|Version' || install_torch
pip show detectron2 | egrep 'Name|Version' || install_detectron2
pip show layoutparser | egrep 'Name|Version' || pip install layoutparser[ocr,paddledetection]==0.2.0

pip show pdbpp || pip install pdbpp

pip install -e .

python fix-paddleocr.py
python fix-detectron2.py
