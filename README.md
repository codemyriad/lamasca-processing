# Newspaper annotation training for lamasca

## Quick Links

- **Open ONI**: [https://oni.cmzx.it/lccn/sn00000001/issues/](https://oni.cmzx.it/lccn/sn00000001/issues/)
- **Annotated Thumbnails**: [https://newspapers.codemyriad.io/lamasca-preview/index.html](https://newspapers.codemyriad.io/lamasca-preview/index.html)

## General Structure

This repository contains code to help with annotating and training a Machine Learning (ML) model for layout recognition of the newspaper *La Masca*.

The process for annotating is:

1. PDF files are uploaded to https://newspapers.codemyriad.io/lamasca/1994/index.html
2. The PDF files are [converted to grayscale images and deskewed](src/lp_labelstudio/preprocess-pdf/cli.py).
3. The results are available in URLs like https://newspapers.codemyriad.io/lamasca-pages/1994/lamasca-1994-01-12/page_01.jpeg
4. The pages are then uploaded to Label Studio using [the `lp-labelstudio labelstudio-api projects create` command](src/lp_labelstudio/labelstudio_api.py#create)
5. Label Studio is used to annotate the pages
6. [The `lp-labelstudio labelstudio-api projects fetch` command](src/lp_labelstudio/labelstudio_api.py#fetch) is used to download the annotations into the `annotations` directory next to the images. For each annotator, a directory is created, and each task (page) is saved as a single file in that directory. All annotations are also incorporated into a `manifest.json` file. For example:
  ```
  /lamasca-pages/1994/lamasca-1994-01-12/
  ├── annotations/
  │   └── annotator@example.com/
  │       ├── page01.json
  │       ├── page02.json
  │       └── ...
  ├── manifest.json
  ├── page_01.jpeg
  ├── page_02.jpeg
  └── ...
  ```
7. If the same issue is uploaded to Label Studio again, it will now include the annotations that have been fetched.

8. [The `generate-thumbnails` command](src/lp_labelstudio/generate_thumbnails.py) can be used to generate thumbnails of the pages with overlaid annotations, [like this one](https://newspapers.codemyriad.io/lamasca-preview/lamasca-1994-01-19/page_01.jpeg).

9. The [Sigal](https://sigal.saimon.org/) gallery generator [has been used to generate HTML galleries](#galleries) of these annotated pages for easy manual checking and observation.

10. A `manifest.json` file is generated for each issue folder. If annotations are already present for the issue, they will be included in the manifest. The manifest is used to generate the COCO JSON file for training. Here's the command used to generate the manifest files:

    ```bash
    lp-labelstudio generate-labelstudio-manifest /tmp/newspapers/lamasca-pages/1994/lamasca-*
    ```

11. To prepare the annotations for training, a COCO JSON file is generated with `lp-labelstudio collect-coco` from [src/lp_labelstudio/collect_coco.py](src/lp_labelstudio/collect_coco.py#collect_coco). This is the command used:

    ```bash
    lp-labelstudio collect-coco $(find /tmp/newspapers/lamasca-pages -name manifest.json -size +100k)
    cp /tmp/coco-out.json /tmp/newspapers/lamasca-pages/1994/coco-all.json
    ```

12. Now the training can start. The `training-image` directory defines a Docker image that can be used to train the model: `ghcr.io/codemyriad/lamasca-layoutparser`. It includes the `prepare-training.sh` script that will prepare and start the training.
* To use vast.ai to run the training, these commands can be quite handy:
  ```bash
  vastai search offers 'dlperf>100 cpu_ram>60 inet_down>1000 inet_up>1000 gpu_name=RTX_4090 num_gpus>=2' -o dph
  # Choose an instance id
  INSTANCEID=000000000
  vastai create instance ${INSTANCEID} --image ghcr.io/codemyriad/lamasca-layoutparser --disk 100 --onstart-cmd "byobu new-session -d -s training 'touch ~/.no_auto_tmux; bash /usr/local/bin/prepare-training.sh'"
  # Wait for the instance to start. Here's an indicator for the terminal (but you can follow on their web UI too)
  watch -n1 "vastai show instances --raw|jq .[].status_msg"
  ssh $(vastai ssh-url $(vastai show instances --raw|jq .[0].id))
  # when connected, run `byobu`
  ```

## Notes

When working on this project, the contents of [https://newspapers.codemyriad.io/](https://newspapers.codemyriad.io/) are mounted on `/tmp/newspapers` using the excellent `rclone` tool. Some code may hardcode this path.

The project package is currently named `lp-labelstudio`, but it's actually very specific to the use case it was developed for. Consider renaming it to reflect its purpose more accurately.

## Galleries

The [Sigal](https://sigal.saimon.org/) gallery generator has been used to generate HTML galleries.

- **Generate Thumbnails with Annotations**:

  ```bash
  lp-labelstudio generate-thumbnails /tmp/newspapers/lamasca-pages/1994/ /tmp/thumbnails
  ```

- **Generate the Gallery**:

  ```bash
  sigal build -c sigal.conf.py /tmp/thumbnails/ /tmp/sigal-thumbnails
  ```

- **Copy the Gallery**:

  ```bash
  cp -r /tmp/sigal-thumbnails/* /tmp/newspapers/lamasca-preview/
  ```
