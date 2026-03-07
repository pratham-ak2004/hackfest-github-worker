freeze:
	pip list --format=freeze > requirements.txt

worker:
	python app.py

flower:
	python app.py --flower

compose:
	docker-compose up -d

dashboard:
	python app.py --dashboard