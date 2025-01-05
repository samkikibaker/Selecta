#!/bin/bash

# Step 1: Build the Docker image
echo "Building Docker image..."
docker build -t song_categoriser .

# Step 2: Open the Streamlit app in the browser automatically
echo "Opening Streamlit app in the browser..."
echn "Note this may be slow to load the first time..."
open http://localhost:8501

# Step 3: Run the Docker container
echo "Running Docker container..."
docker run --mount type=bind,source=$(pwd)/songs,target=/app/songs --mount type=bind,source=$(pwd)/cache,target=/app/cache -p 8501:8501 song_categoriser

