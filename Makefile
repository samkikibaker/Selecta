docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af

ruff:
	uv run ruff check . --fix
	uv run ruff format

run_api:
	cd src && cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8080
	# cd src && cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8080 --reload

build_app:
	# uv run pyinstaller --noconfirm --onedir --windowed Selecta.py
	uv run pyinstaller selecta.spec --noconfirm

run_app:
	/Users/sambaker/Documents/GitHub/Selecta/dist/Selecta/Selecta

remove_workflow_runs:
	for run_id in $(gh run list --limit 1000 --json databaseId -q '.[].databaseId'); do
	  gh run delete $run_id
	done
