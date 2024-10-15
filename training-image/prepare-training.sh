#!/usr/bin/env bash

curl https://newspapers.codemyriad.io/lamasca-pages/1994/coco-all.json > /tmp/coco-out.json

cd /tmp
grep "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers" /tmp/coco-out.json |sed -e 's/.*"file_name": "//;s/".*//;s|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers|https://newspapers.codemyriad.io|' | xargs wget -m -c

ln -s /tmp/newspapers.codemyriad.io/ /tmp/newspapers

cp /tmp/coco-out.json /tmp/coco-local.json

sed -i -e 's|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:|/tmp/|' /tmp/coco-local.json

cd /training
python3 utils/cocosplit.py --annotation-path  /tmp/coco-local.json  --train /tmp/train.json --test /tmp/test.json --split-ratio 0.8

echo Preparations done.
echo Running training...
set +x
python3 tools/train_net.py --image_path_train /tmp/train_images --image_path_val /tmp/validation_images  --dataset_name "my_dataset" --json_annotation_train /tmp/train.json --json_annotation_val /tmp/test.json --config-file base-model/config.yml MODEL.WEIGHTS base-model/model_final.pth OUTPUT_DIR /tmp/trained MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE 256 SOLVER.CHECKPOINT_PERIOD 20000 SOLVER.MAX_ITER 80000 SOLVER.IMS_PER_BATCH 2
