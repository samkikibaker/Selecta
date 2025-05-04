docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af

ruff_fix:
	uv tool run ruff check --fix
	uv tool run ruff format

streamlit:
	streamlit run streamlit/streamlit_app.py

run_api:
	cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8080

