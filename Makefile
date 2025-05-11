docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af

ruff:
	uv run ruff format

streamlit:
	streamlit run streamlit/streamlit_app.py

run_api:
	cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8080

IMAGE_NAME=selecta
TAG=latest
REGISTRY=crselecta.azurecr.io
push:
	@echo "Building and pushing $(IMAGE_NAME):$(TAG) to $(REGISTRY)"
	docker build --platform linux/amd64 -t $(REGISTRY)/$(IMAGE_NAME):$(TAG) .
	az acr login --name $(subst .azurecr.io,,$(REGISTRY))
	docker push $(REGISTRY)/$(IMAGE_NAME):$(TAG)


