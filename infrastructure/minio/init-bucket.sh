#!/bin/sh
set -e

echo "Configuring MinIO client..."
mc alias set local http://minio:9000 "${S3_ACCESS_KEY:-minioadmin}" "${S3_SECRET_KEY:-minioadmin123}"

BUCKET_NAME="${S3_BUCKET_NAME:-claimguard-documents}"
echo "Ensuring bucket '${BUCKET_NAME}' exists..."
mc mb --ignore-existing "local/${BUCKET_NAME}"

echo "Enforcing private bucket access policy..."
mc anonymous set none "local/${BUCKET_NAME}"

echo "MinIO initialization completed successfully."
exit 0
