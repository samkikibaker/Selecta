#!/bin/bash

# Step 1: Build the Docker image
echo "Building Docker image..."
docker build -t song_categoriser .

# Step 2: Run the Docker container
echo "Running Docker container..."
docker run --shm-size=14g --cpus=8 --mount type=bind,source=$(pwd)/songs,target=/app/songs --mount type=bind,source=$(pwd)/cache,target=/app/cache -p 8501:8501 song_categoriser
