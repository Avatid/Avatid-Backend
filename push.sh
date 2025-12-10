#!/bin/bash
gcloud auth configure-docker \
    europe-west2-docker.pkg.dev
# Registry path
REGISTRY=""


# Build and push the API image
echo "Building and pushing API image with test tag"

# Build the API images
docker build -f Dockerfile -t $REGISTRY/api:test .

# Push the API images
echo "Pushing API images to $REGISTRY..."
docker push $REGISTRY/api:test

# Build the Celery images
echo "Building and pushing Celery image with test tag"
docker build -f celery.dockerfile -t $REGISTRY/celery:test .

# Push the Celery images
echo "Pushing Celery images to $REGISTRY..."
docker push $REGISTRY/celery:test

echo "Successfully pushed images:"
echo "- $REGISTRY/api:test"
echo "- $REGISTRY/celery:test"