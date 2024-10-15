#!/usr/bin/env bash

curl https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/coco-all.json > /tmp/coco-out.json

cd /tmp
grep "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers" /tmp/coco-out.json |sed -e 's/.*"file_name": "//;s/".*//' | xargs wget -m -c

ln -s /tmp/eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a\:newspapers/ /tmp/newspapers

cp /tmp/coco-out.json /tmp/coco-local.json

sed -i -e 's|https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:|/tmp/|' /tmp/coco-local.json
