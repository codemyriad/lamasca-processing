#!/usr/bin/env bash

aria2c -d /tmp -c https://newspapers.codemyriad.io/lamasca-pages/1994/coco-all.json

grep "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers" /tmp/coco-all.json |sed -e 's/.*"file_name": "//;s/".*//;s|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers|https://newspapers.codemyriad.io|'| sort > /tmp/urls.txt

mkdir -p /tmp/newspapers
cd /tmp/newspapers

declare -A dir_urls
CONCURRENT_DOWNLOAD_NUM=8

# Read URLs and group them by directory
while IFS= read -r url; do
  # Extract the path after the domain (assuming URLs start with http(s)://domain/)
  # Adjust the cut command based on your URL structure if needed
  path=$(echo "$url" | cut -d'/' -f4-)
  # Get the directory name from the path
  dir=$(dirname "$path")
  # Append the URL to the list for this directory
  # Use a newline as a separator
  dir_urls["$dir"]+="$url"$'\n'
done < "../urls.txt"

# Function to download URLs for a specific directory
download_directory() {
  local dir="$1"
  local urls="$2"
  # Create the directory if it doesn't exist
  mkdir -p "$dir"
  echo Created $dir
  # Write URLs to the list file
  echo "$urls" > "$dir/urls.txt"
  # Run aria2c with the list file
  aria2c \
    -d "$dir" `# Set download directory` \
    -j$CONCURRENT_DOWNLOAD_NUM `# Number of concurrent downloads` \
    -i "$dir/urls.txt" `# Input file with URLs` \
    -c `# Continue incomplete downloads` \
    --retry-wait=1 `# Wait time between retries` \
    --max-tries=5 `# Maximum number of retries` \
    --log="$dir/aria2c.log" # Log file for debugging
}

# Iterate over each directory and initiate downloads
for dir in "${!dir_urls[@]}"; do
  # Get the URLs for this directory
  urls="${dir_urls[$dir]}"
  # Download the files for this directory
  download_directory "$dir" "$urls"
done


cp /tmp/coco-out.json /tmp/coco-local.json

sed -i -e 's|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:|/tmp/|' /tmp/coco-local.json

mkdir /training/base-model
aria2c -d /training/base-model https://newspapers.codemyriad.io/lamasca-training/base-model/config.yml https://newspapers.codemyriad.io/lamasca-training/base-model/model_final.pth > base-model/model_final.pth

cd /training
python3 utils/cocosplit.py --annotation-path  /tmp/coco-local.json  --train /tmp/train.json --test /tmp/test.json --split-ratio 0.8

echo Preparations done.
echo Running training...
set +x
torchrun tools/train_net.py --image_path_train /tmp/train_images --image_path_val /tmp/validation_images  --dataset_name "my_dataset" --json_annotation_train /tmp/train.json --json_annotation_val /tmp/test.json --config-file base-model/config.yml MODEL.WEIGHTS base-model/model_final.pth OUTPUT_DIR /tmp/trained MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE 256 SOLVER.CHECKPOINT_PERIOD 20000 SOLVER.MAX_ITER 80000 SOLVER.IMS_PER_BATCH 2
