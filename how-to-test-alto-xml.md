# How to test an Alto XML file

Setup Open ONI as submodule. This is needed since the open-oni folder will be mounted in the `web` container.

    `git submodule --init --checkout`

Than you should be able to test an XML Alto file with:

    `bash test_alto_batch.sh <path_to_alto_XML_file>`

The script will lookup for a .jp2 and .tif image in the same directory and with the same name as the Alto XML file.

    e.g.

    test_alto
        |-- 0001.xml
        |-- 0001.jp2
        |-- 0001.tif
