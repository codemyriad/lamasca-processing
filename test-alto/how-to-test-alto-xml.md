# How to test an Alto XML file

Setup Open ONI as submodule. This is needed since the open-oni folder will be mounted in the `web` container.

```bash
git submodule update --init --checkout
```

Than you should be able to test an XML Alto file with:

```
bash test-alto-batch.sh <path_to_alto_XML_file>`

# e.g.
bash test-alto-batch.sh example-file/0001.xml
```

You may need to set up a [Github Personal access token
(classic)](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-with-a-personal-access-token-classic)
to be able to pull the Docker image referred to in
[`docker-compose.yml`](./docker-compose.yml).

You can also control which HTTP port the Docker container will serve
on by setting the `HTTPPORT` environment variable prior to executing
`test-alto-batch.sh`:

```bash
# e.g.
export HTTPPORT=9090
bash test-alto-batch.sh example-file/0001.xml
```

If you need to re-run the script, you might want to make sure that all
containers are shut down first by running:

```bash
docker compose down
```

The `test-alto-batch.sh` script will lookup for a .jpeg image in the same directory and with the same name as the Alto XML file.

```
e.g.

example-file
    |-- 0001.xml
    |-- 0001.jpeg
```


Data reset
----------

To reset local state run

    docker compose down
    docker volume rm test-alto_data-solr test-alto_data-mariadb
