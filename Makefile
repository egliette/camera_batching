.PHONY: attach down up build

attach:
	docker compose down
	docker compose up -d
	docker compose exec -it camera_batching /bin/bash

down:
	docker compose down

up:
	docker compose up -d

build:
	docker compose build
