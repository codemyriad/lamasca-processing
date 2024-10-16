#!/usr/bin/env bash

# This script is meant to be invoked on vast.ai (or other provider) instance creation
# Here's an example vast.ai invocation:
# vastai create instance $INSTANCE_ID --image ghcr.io/codemyriad/lamasca-layoutparser --disk 100 --onstart-cmd "byobu new-session -d -s training 'touch ~/.no_auto_tmux; bash /usr/local/bin/prepare-training.sh'"
# and here's a snippet to monitor the machine provisioning:
# watch -n1 "vastai show instances --raw|jq .[0].status_msg"
# and one to connect (in case it's the first/only active instance):
# ssh (vastai ssh-url (vastai show instances --raw|jq .[0].id))


# Exit early in case of errors
set -euo pipefail
error_handler() {
    echo "An error occurred. Sleeping for 24 hours..."
    sleep 86400
}
# But make sure the byobu terminal where we were invoked does not disappear
trap error_handler ERR

# Download COCO JSON file
aria2c -d /tmp -c https://newspapers.codemyriad.io/lamasca-pages/1994/coco-all.json

# Extract and transform URLs
grep "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers" /tmp/coco-all.json | \
    sed -e 's/.*"file_name": "//;s/".*//;s|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers|https://newspapers.codemyriad.io|' | \
    sort > /tmp/urls.txt

# Prepare directories
mkdir -p /tmp/newspapers
cd /tmp/newspapers

declare -A dir_urls
CONCURRENT_DOWNLOAD_NUM=8

# Read URLs and group them by directory
while IFS= read -r url; do
    path=$(echo "$url" | cut -d'/' -f4-)
    dir=$(dirname "$path")
    dir_urls["$dir"]+="$url"$'\n'
done < "../urls.txt"

# Function to download URLs for a specific directory
download_directory() {
    local dir="$1"
    local urls="$2"
    mkdir -p "$dir"
    echo "Created $dir"
    echo "$urls" > "$dir/urls.txt"
    aria2c \
        -d "$dir" \
        -j"$CONCURRENT_DOWNLOAD_NUM" \
        -i "$dir/urls.txt" \
        -c \
        --retry-wait=1 \
        --max-tries=5 \
        --log="$dir/aria2c.log"
}

# Iterate over each directory and initiate downloads
for dir in "${!dir_urls[@]}"; do
    urls="${dir_urls[$dir]}"
    download_directory "$dir" "$urls"
done

# Prepare local COCO JSON
cp /tmp/coco-all.json /tmp/coco-local.json
sed -i -e 's|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:|/tmp/|' /tmp/coco-local.json

# Download base model
aria2c -d /training/base-model https://newspapers.codemyriad.io/lamasca-training/base-model/model_final.pth

# Split dataset
cd /training
python3 utils/cocosplit.py \
    --annotation-path /tmp/coco-local.json \
    --train /tmp/train.json \
    --test /tmp/test.json \
    --split-ratio 0.9

echo "Preparations done."
echo "Running training..."

# Count GPUs
NUMGPUS=$(nvidia-smi -L | wc -l)

# Run training
python3 tools/train_net.py \
    --num-gpus "$NUMGPUS" \
    --image_path_train /tmp/train_images \
    --image_path_val /tmp/validation_images \
    --dataset_name "lamasca" \
    --json_annotation_train /tmp/train.json \
    --json_annotation_val /tmp/test.json \
    --config-file base-model/config.yml \
    MODEL.WEIGHTS base-model/model_final.pth \
    OUTPUT_DIR /tmp/trained \
    MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE 256 \
    SOLVER.CHECKPOINT_PERIOD 20000 \
    SOLVER.MAX_ITER 80000 \
    SOLVER.BASE_LR 0.02 \
    SOLVER.IMS_PER_BATCH "$NUMGPUS"
