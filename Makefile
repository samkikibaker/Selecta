docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af
