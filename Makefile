test:
	pytest -q

run:
	python run.py .dogfood.toml

up:
	docker compose up --build

down:
	docker compose down
