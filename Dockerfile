FROM python:3.10-slim

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

# Copy all files to the container
COPY backend backend
COPY cache cache
COPY src src
COPY yamnet-tensorflow2-yamnet-v1 yamnet-tensorflow2-yamnet-v1
COPY .pre-commit-config.yaml .
COPY .python-version .
COPY main.py .
COPY pyproject.toml .

# Install dependencies from the pyproject.toml file
RUN uv sync

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Command to run the Streamlit app
CMD ["python", "main.py"]

