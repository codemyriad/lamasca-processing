#!/bin/bash

curl -X POST http://localhost:9090/predict \
     -H "Content-Type: application/json" \
     -d '{
           "task": {
             "data": {
               "image": "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-01-26/page_16.jpeg"
             }
           }
         }'
