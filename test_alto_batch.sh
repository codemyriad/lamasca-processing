#!/bin/bash

set -e
set -x

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <alto_xml_file>"
    exit 1
fi

# Input Alto XML file
ALTO_XML_FILE=$(realpath "$1")
ALTO_XML_FILENAME=$(basename "${ALTO_XML_FILE%.*}")

# Create temporary batch directory structure
BATCH_DIR=./test_batches
BATCH_NAME="batch_lamasca_${ALTO_XML_FILENAME}_ver01"
BATCH_DATE=1994011201

echo "Creating test batch in ${BATCH_DIR}/${BATCH_NAME}"

# Create Open ONI batch directory structure
mkdir -p "${BATCH_DIR}/${BATCH_NAME}/data/sn00000001/001/${BATCH_DATE}"

# Copy Alto XML to batch directory
cp "$ALTO_XML_FILE" "${BATCH_DIR}/${BATCH_NAME}/data/sn00000001/001/${BATCH_DATE}/0001.xml"

# Create a dummy batch_xml file (required for Open ONI batch)
cat << EOF > "${BATCH_DIR}/${BATCH_NAME}/data/batch.xml"
<?xml version="1.0" ?>
<batch xmlns="http://www.loc.gov/ndnp" name="${ALTO_XML_FILENAME}" awardee="lamasca" awardYear="1994">
	<issue editionOrder="01" issueDate="1994-01-12" lccn="sn00000001">./sn00000001/001/${BATCH_DATE}/${BATCH_DATE}.xml</issue>
</batch>
EOF

# Copy default mets file
cp test_batches/default_mets.xml ${BATCH_DIR}/${BATCH_NAME}/data/sn00000001/001/${BATCH_DATE}/${BATCH_DATE}.xml

# Create a dummy image to satisfy Open ONI requirements
convert -size 2000x3000 xc:white "${BATCH_DIR}/${BATCH_NAME}/data/sn00000001/001/${BATCH_DATE}/0001.jp2"
convert -size 2000x3000 xc:white "${BATCH_DIR}/${BATCH_NAME}/data/sn00000001/001/${BATCH_DATE}/0001.tif"

# Path to Open ONI docker-compose file (adjust as needed)
DOCKER_COMPOSE_PATH="./docker-compose.yml"

# Ensure docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_PATH" ]; then
    echo "Docker Compose file not found at $DOCKER_COMPOSE_PATH"
    exit 1
fi

# Stop any existing Open ONI containers
docker compose -f "$DOCKER_COMPOSE_PATH" down

# Start Docker Compose with batch mounted
docker compose -f "$DOCKER_COMPOSE_PATH" up -d

# Wait for the container to fully start
sleep 15

# Change permissions for the django cache
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "chown -R www-data:www-data /var/tmp/django_cache"

# Create Awardee and Title objects if they don't exists
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "source ENV/bin/activate && python manage.py shell < /opt/create_awardee_title.py"

# Purge the batch if it exists in Open ONI
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "source ENV/bin/activate && python manage.py purge_batch $BATCH_NAME"

# Load the batch into Open ONI
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "source ENV/bin/activate && python manage.py load_batch /opt/openoni/data/batches/$BATCH_NAME"

echo "Batch ${BATCH_NAME} loaded successfully!"

echo "You should be able to see your page at http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/"
echo "Useful links:"
echo "OCR: http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/ocr/"
echo "Text coordinates: http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/coordinates/"
