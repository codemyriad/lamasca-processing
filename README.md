Newspaper annotation training for lamasca
=========================================

Quick links
-----------

* Open Oni: https://oni.cmzx.it/lccn/sn00000001/issues/
* Annotated thumbnails: https://newspapers.codemyriad.io/lamasca-preview/index.html

General structure
-----------------

This repository contains code to help with annotating and training an ML model for layout recognition of the newspaper "la masca".

The process for annotating is:

* PDF files are uploaded to https://newspapers.codemyriad.io/lamasca/1994/index.html
* The PDF files are [converted to grayscale images and deskewed](src/lp_labelstudio/preprocess-pdf/cli.py).
* The results are available in URLs like https://newspapers.codemyriad.io/lamasca-pages/1994/lamasca-1994-01-12/page_01.jpeg
* The pages are then uploaded to Label Studio using [the `lp-labelstudio labelstudio-api projects create` command](src/lp_labelstudio/labelstudio_api.py#create)
* Label Studio is used to annotate the pages
* [The `lp-labelstudio labelstudio-api projects fetch` command](src/lp_labelstudio/labelstudio_api.py#fetch) is used to download the annotations into the "annotations" directory next to the images. For each annotator a directory is created, and each task (page) is saved as a single file in that page. All annotations are also incorporated in a `manifest.json` file. For example:
  ```
  /lamasca-pages/1994/lamasca-1994-01-12/
  /lamasca-pages/1994/lamasca-1994-01-12/annotations
  /lamasca-pages/1994/lamasca-1994-01-12/annotations/annotator.example.com
  /lamasca-pages/1994/lamasca-1994-01-12/annotations/annotator.example.com/page01.json
  /lamasca-pages/1994/lamasca-1994-01-12/annotations/annotator.example.com/page02.json
  ...
  /lamasca-pages/1994/lamasca-1994-01-12/manifest.json
  /lamasca-pages/1994/lamasca-1994-01-12/page_01.jpeg
  /lamasca-pages/1994/lamasca-1994-01-12/page_02.jpeg
  ...
  ```
* If the same issue is uploaded to Label Studio again, it will now include the annotations that have been fetched.
* [The `generate-thumbnails` command](src/lp_labelstudio/generate_thumbnails.py) can be used to generate thumbnails of the pages with overlayed annotations, [like this one](https://newspapers.codemyriad.io/lamasca-preview/lamasca-1994-01-19/page_01.jpeg).
* The [sigal](https://sigal.saimon.org/) gallery generator [has been used to generate HTML galleries](#galleries) of these annotated pages for easy manual checking/observing.
* A `manifest.json` file is generated for each issue folder. If annotations are already present for the issue, they will be included in the manifest. The manifest is used to generate the coco JSON file for training. Here's the command I use to generate the manifest files: `lp-labelstudio generate-labelstudio-manifest /tmp/newspapers/lamasca-pages/1994/lamasca-*`.
* To preapre the annotations for training, a coco JSON file is generated with `lp-labelstudio collect-coco` from [src/lp_labelstudio/collect_coco.py](src/lp_labelstudio/collect_coco.py#collect_coco). This is the command I use: `lp-labelstudio collect-coco (find /tmp/newspapers/lamasca-pages -name manifest.json -size +100k); cp /tmp/coco-out.json /tmp/newspapers/lamasca-pages/1994/coco-all.json`.
* Now the training can start: the `training-image` directory defines a docker image that can be used to train the model: `ghcr.io/codemyriad/lamasca-layoutparser`. It includes the `prepare-training.sh` script that will prepare and start the training.
* To use vast.ai to run the training, these commands can be quite handy:
  ```
  vastai search offers 'dlperf>100 cpu_ram>60 inet_down>1000 inet_up>1000 gpu_name=RTX_4090 num_gpus>=2' -o dph
  # Choose an instance id
  INSTANCEID=000000000
  vastai create instance ${INSTANCEID} --image ghcr.io/codemyriad/lamasca-layoutparser --disk 100 --onstart-cmd "byobu new-session -d -s training 'touch ~/.no_auto_tmux; bash /usr/local/bin/prepare-training.sh'"
  # Wait for the instance to start. Here's an indicator for the terminal (but you can follow on their web UI too)
  watch -n1 "vastai show instances --raw|jq .[].status_msg"
  ssh $(vastai ssh-url $(vastai show instances --raw|jq .[0].id))
  # when connected, run `byobu`
  ```

Notes
-----

When working on this I have the contents of https://newspapers.codemyriad.io/ mounted on /tmp/newspapers thanks to the excellent rclone tool. The code sometimes hardcodes this.

Naming is sometimes very bad. The project package is currently called "lp-labelstudio". But it's actually very specific to the use case it was developed for.

Galleries
---------

The [sigal](https://sigal.saimon.org/) gallery generator has been used to generate HTML galleries.
* Generate thumbnails with annotations: `lp-labelstudio generate-thumbnails /tmp/newspapers/lamasca-pages/1994/ /tmp/thumbnails`
* Generate the gallery: `sigal build -c sigal.conf.py /tmp/thumbnails/ /tmp/sigal-thumbnails`
* Copy the gallery: `cp -rv /tmp/sigal-thumbnails/* /tmp/newspapers/lamasca-preview/`
