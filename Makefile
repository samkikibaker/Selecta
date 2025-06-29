docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af

ruff:
	uv run ruff check . --fix
	uv run ruff format

run_api:
	# cd src && cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8080
	cd src && cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8080 --reload



build_app:
	# uv run pyinstaller --noconfirm --onedir --windowed Selecta.py
	uv run pyinstaller selecta.spec --noconfirm

build_disk_image:
	make build_app && ./build_disk_image.sh

run_app:
	/Applications/Selecta.app/Contents/MacOS/Selecta
	# open /Applications/Selecta.app
