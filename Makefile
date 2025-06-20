docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af

ruff:
	uv run ruff check . --fix
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

run_local:
	@echo "Building and running local $(IMAGE_NAME):$(TAG)"
	docker build --platform linux/amd64 -t $(IMAGE_NAME):$(TAG) .
	docker run --rm -it $(IMAGE_NAME):$(TAG)

build_app:
	# First run this
	# uv run pyinstaller --noconfirm --onedir --windowed selecta.py
	# Then manually enter the datas in the .spec
	# datas=[("src/selecta/yamnet-tensorflow2-yamnet-v1", "yamnet-tensorflow2-yamnet-v1")]
	# Then run this each time after that
	uv run pyinstaller selecta.spec


build_disk_image:
	make build_app
	./build_disk_image.sh
