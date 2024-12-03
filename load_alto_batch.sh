#!/bin/bash

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <alto_xml_file>"
    exit 1
fi

# Input Alto XML file
ALTO_XML_FILE=$(realpath "$1")

# Create temporary batch directory structure
BATCH_DIR=$(mktemp -d)
BATCH_NAME=$(basename "${ALTO_XML_FILE%.*}")

# Create Open ONI batch directory structure
mkdir -p "${BATCH_DIR}/${BATCH_NAME}/alto"
mkdir -p "${BATCH_DIR}/${BATCH_NAME}/jp2"
mkdir -p "${BATCH_DIR}/${BATCH_NAME}/tiff"

# Copy Alto XML to batch directory
cp "$ALTO_XML_FILE" "${BATCH_DIR}/${BATCH_NAME}/alto/"

# Create a dummy mets.xml file (required for Open ONI batch)
cat << EOF > "${BATCH_DIR}/${BATCH_NAME}/mets.xml"
<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink">
    <mets:dmdSec ID="dmdSec_1">
        <mets:mdWrap MDTYPE="DC">
            <mets:xmlData>
                <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">${BATCH_NAME}</dc:title>
            </mets:xmlData>
        </mets:mdWrap>
    </mets:dmdSec>
</mets:mets>
EOF

# Create a dummy image to satisfy Open ONI requirements
convert -size 2000x3000 xc:white "${BATCH_DIR}/${BATCH_NAME}/jp2/${BATCH_NAME}_0001.jp2"
convert -size 2000x3000 xc:white "${BATCH_DIR}/${BATCH_NAME}/tiff/${BATCH_NAME}_0001.tif"

# Path to Open ONI docker-compose file (adjust as needed)
DOCKER_COMPOSE_PATH="/path/to/open-oni/docker-compose.yml"

# Ensure docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_PATH" ]; then
    echo "Docker Compose file not found at $DOCKER_COMPOSE_PATH"
    exit 1
fi

# Stop any existing Open ONI containers
docker-compose -f "$DOCKER_COMPOSE_PATH" down

# Start Docker Compose with batch mounted
docker-compose -f "$DOCKER_COMPOSE_PATH" up -d

# Wait for the container to fully start
sleep 15

# Load the batch into Open ONI
docker-compose -f "$DOCKER_COMPOSE_PATH" exec -T web python manage.py load_batch /opt/newspaper_batches/"$BATCH_NAME"

echo "Batch ${BATCH_NAME} loaded successfully!"
