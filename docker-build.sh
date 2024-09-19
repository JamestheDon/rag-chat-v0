#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY environment variable is not set."
  exit 1
fi

# Build the Docker image, passing the OPENAI_API_KEY as a secret
# Run the docker build command using eval to handle quoted values
eval docker buildx build \
  --secret id=OPENAI_API_KEY,env=OPENAI_API_KEY \
  --platform=linux/amd64,linux/arm64 \
  -t rag-chat-v0-container/rag-chat-v0:latest \
  --load \
  .

echo "Docker image 'rag-chat-v0-container/rag-chat-v0:latest' built successfully."
