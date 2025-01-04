# Makefile for Docker cleanup tasks

# Define a target to prune unused Docker images
docker_clean:
	# Remove unused images, containers, volumes, and networks
	docker system prune -af
