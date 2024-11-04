deps:
	poetry install

up:
	docker-compose up -d --build --force-recreate

down:
	docker-compose down

migrate:
	python manage.py makemigrations
	python manage.py migrate

dev:
	python manage.py runserver