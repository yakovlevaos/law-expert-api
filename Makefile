deps:
	poetry install

up:
	docker-compose --profile prod up -d --build --force-recreate

up_db:
	docker-compose --profile dev up -d --build --force-recreate

down:
	docker-compose --profile prod down
	docker-compose --profile dev down
	docker-compose down

migrate:
	python manage.py makemigrations
	python manage.py migrate

dev:
	python manage.py runserver

dump:
	docker exec -i genesis-postgres /bin/bash -c "pg_dump --username postgres genesis" > ./volumes/dump_051124.sql

restore:
	cat ./volumes/dump_051124.sql | docker exec -i genesis-postgres psql -U postgres --dbname=genesis