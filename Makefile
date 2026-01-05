go:
	docker-compose build etl
	docker-compose up -d localstack postgres
	docker-compose run --rm etl

down:
	docker-compose down