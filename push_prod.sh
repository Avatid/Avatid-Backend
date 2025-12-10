#!/bin/bash

# Registry path
REGISTRY=""

# Check if we're on master branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "master" ]; then
    echo "Error: Must be on master branch to push production images"
    exit 1
fi

# Check if there are any uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory is not clean. Commit all changes before pushing production images"
    exit 1
fi

echo "Building and pushing production images..."

# Build and push the API image
echo "Building API production image..."
docker build -f Dockerfile -t $REGISTRY/api:prod .

# Push the API image
echo "Pushing API production image to $REGISTRY..."
docker push $REGISTRY/api:prod

# Build and push the Celery image
echo "Building Celery production image..."
docker build -f celery.dockerfile -t $REGISTRY/celery:prod .

# Push the Celery image
echo "Pushing Celery production image to $REGISTRY..."
docker push $REGISTRY/celery:prod

echo "Successfully pushed production images:"
echo "- $REGISTRY/api:prod"
echo "- $REGISTRY/celery:prod"