.ONESHELL:
SHELL := /bin/bash

setup:
	echo "Installing uv from Astral..."
	unameOut=$$(uname -s); \
	if [ "$$unameOut" = "Darwin" ] || [ "$$unameOut" = "Linux" ]; then \
		echo "Detected Unix-like OS: $$unameOut"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	elif [ "$$OS" = "Windows_NT" ]; then \
		echo "Detected Windows OS"; \
		powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"; \
	else \
		echo "Unsupported OS: $$unameOut"; \
		exit 1; \
	fi; \
	uv sync

format:
	uv run ruff check . --fix
	uv run ruff format

run:
	uv run Selecta.py