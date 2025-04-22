docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af

ruff_fix:
	uv tool run ruff check --fix
	uv tool run ruff format

streamlit:
	streamlit run app.py