FROM python:3.9-slim

# The uv installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download the latest uv installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the uv installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy only necessary files to the container
COPY app.py .
COPY pyproject.toml .
COPY src/selecta/SongCategoriser.py .
COPY src/selecta/yamnet-tensorflow2-yamnet-v1 yamnet-tensorflow2-yamnet-v1
COPY logs logs

# Create directories for cache, songs and playlists
RUN mkdir -p /app/cache /app/songs /app/playlists

# Install dependencies from the pyproject.toml file
RUN uv sync

# Expose the Streamlit port
EXPOSE 8501

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variable in Dockerfile
ENV IN_CONTAINER=true

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
