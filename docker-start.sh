#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure that OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY is not set."
  echo "Please set the OPENAI_API_KEY environment variable before running this script."
  exit 1
fi

# Set the ENVIRONMENT variable to 'production' if not already set
ENVIRONMENT=${ENVIRONMENT:-production}

# Define the container name and image
CONTAINER_NAME="rag-chat-v0-container"
IMAGE_NAME="rag-chat-v0-container/rag-chat-v0:latest"

# Run the Docker container
docker run -d \
  -p 80:80 \
  --name "$CONTAINER_NAME" \
  -e ENVIRONMENT="$ENVIRONMENT" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  "$IMAGE_NAME"
