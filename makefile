freeze:
	pip list --format=freeze > requirements.txt

worker:
	python app.py

flower:
	python app.py --flower

compose:
	docker-compose up -d

dashboard:
	fastapi run server.py