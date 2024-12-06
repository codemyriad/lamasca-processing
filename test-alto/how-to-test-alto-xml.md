# How to test an Alto XML file

Setup Open ONI as submodule. This is needed since the open-oni folder will be mounted in the `web` container.

    `git submodule update --init --checkout`

Than you should be able to test an XML Alto file with:

    `bash test-alto-batch.sh <path_to_alto_XML_file>`

    e.g.

    `bash test-alto-batch.sh test-alto/0001.xml`

The script will lookup for a .jpeg image in the same directory and with the same name as the Alto XML file.

    e.g.

    test_alto
        |-- 0001.xml
        |-- 0001.jpeg

One can reset all data by removing the docker peristent volumes `data-mariadb` and `data-solr`.


Data reset
----------

To reset local state run

    docker compose down
    docker volume rm test-alto_data-solr test-alto_data-mariadb
