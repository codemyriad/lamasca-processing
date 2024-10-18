#!/usr/bin/env bash

lp-labelstudio labelstudio-api projects fetch
lp-labelstudio generate-labelstudio-manifest /tmp/newspapers/lamasca-pages/1994/lamasca-*
rm -r /tmp/thumbnails /tmp/sigal-thumbnails/
lp-labelstudio generate-thumbnails /tmp/newspapers/lamasca-pages/1994/ /tmp/thumbnails
sigal build -c sigal.conf.py /tmp/thumbnails/ /tmp/sigal-thumbnails
rsync -r --inplace -v /tmp/sigal-thumbnails/* /tmp/newspapers/lamasca-preview/
