#!/bin/bash

set -e
cd "$(dirname "$0")"

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <alto_xml_file>"
    exit 1
fi

# Input Alto XML file
ALTO_XML_FILE=$(realpath "$1")
ALTO_XML_DIR=$(dirname "${ALTO_XML_FILE}")
ALTO_XML_FILENAME=$(basename "${ALTO_XML_FILE%.*}")
JPEG_FILE="${ALTO_XML_DIR}/${ALTO_XML_FILENAME}.jpeg"

BATCH_DIR=./test_batches
BATCH_NAME="batch_lamasca_${ALTO_XML_FILENAME}_ver01"
BATCH_DATE=1994011201

ALTO_OUTPUT_DIR=${BATCH_DIR}/${BATCH_NAME}/data/sn00000001/001/${BATCH_DATE}

echo "Creating test batch in ${BATCH_DIR}/${BATCH_NAME}"

# Create Open ONI batch directory structure
mkdir -p $ALTO_OUTPUT_DIR

# Copy Alto XML to batch directory
cp "$ALTO_XML_FILE" "${ALTO_OUTPUT_DIR}/0001.xml"

if [ -f "$JPEG_FILE" ]; then
    echo "Found JPEG file: $JPEG_FILE"

    # Define output file paths
    TIFF_FILE="${ALTO_OUTPUT_DIR}/${ALTO_XML_FILENAME}.tif"
    JP2_FILE="${ALTO_OUTPUT_DIR}/${ALTO_XML_FILENAME}.jp2"

    # Check if TIFF file exists
    if [ -f "$TIFF_FILE" ]; then
        echo "TIFF file already exists: $TIFF_FILE"
    else
        # Convert JPEG to TIFF
        convert "$JPEG_FILE" "$TIFF_FILE"
        echo "Converted to TIFF: $TIFF_FILE"
    fi

    # Check if JP2 file exists
    if [ -f "$JP2_FILE" ]; then
        echo "JP2 file already exists: $JP2_FILE"
    else
        # Convert JPEG to JP2
        convert "$JPEG_FILE" "$JP2_FILE"
        echo "Converted to JP2: $JP2_FILE"
    fi

else
  echo "Error: JPEG file not found at ${JPEG_FILE}. You won't see any image!"
fi

# Create a dummy batch_xml file (required for Open ONI batch)
cat << EOF > "${BATCH_DIR}/${BATCH_NAME}/data/batch.xml"
<?xml version="1.0" ?>
<batch xmlns="http://www.loc.gov/ndnp" name="${ALTO_XML_FILENAME}" awardee="lamasca" awardYear="1994">
	<issue editionOrder="01" issueDate="1994-01-12" lccn="sn00000001">./sn00000001/001/${BATCH_DATE}/${BATCH_DATE}.xml</issue>
</batch>
EOF

# Copy default mets file
cp test_batches/default_mets.xml ${ALTO_OUTPUT_DIR}/${BATCH_DATE}.xml

# Path to Open ONI docker-compose file (adjust as needed)
DOCKER_COMPOSE_PATH="./docker-compose.yml"

# Ensure docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_PATH" ]; then
    echo "Docker Compose file not found at $DOCKER_COMPOSE_PATH"
    exit 1
fi

# Start Docker Compose with batch mounted
docker compose -f "$DOCKER_COMPOSE_PATH" up -d

# Wait for the container to fully start
timeout=90
until docker compose logs web | grep -q "ONI setup successful"; do
 if [ $timeout -le 0 ]; then
   echo "Timeout waiting for ONI setup"
   exit 1
 fi
 sleep 3
 timeout=$((timeout-5))
done

# Create Awardee and Title objects if they don't exists
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "source ENV/bin/activate && python manage.py shell < /opt/create_awardee_title.py"

# Purge the batch if it exists in Open ONI
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "source ENV/bin/activate && (python manage.py batches | grep -q '^$BATCH_NAME$' && python manage.py purge_batch $BATCH_NAME; true)"

# Load the batch into Open ONI
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "source ENV/bin/activate && python manage.py load_batch /opt/openoni/data/batches/$BATCH_NAME"

docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "curl -s http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/ > /dev/null"

# Change permissions for the django cache
docker compose -f "$DOCKER_COMPOSE_PATH" exec -T web bash -c "chown -R www-data:www-data /var/tmp/django_cache"

echo ""
echo "Batch ${BATCH_NAME} loaded successfully!"
echo ""
echo "You should be able to see your page at http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/"
echo ""
echo "Useful links:"
echo "OCR: http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/ocr/"
echo "Loaded Alto XML: http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/ocr.xml"
echo "Text coordinates: http://localhost/lccn/sn00000001/1994-01-12/ed-1/seq-1/coordinates/"
