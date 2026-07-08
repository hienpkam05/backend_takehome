build:
	docker compose build

up:
	docker compose up -d

migrate:
	docker compose exec web python manage.py migrate

test:
	docker compose exec web pytest -q

shell:
	docker compose exec web python manage.py shell

down:
	docker compose down
