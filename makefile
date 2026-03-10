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

test:
	echo "Select the test to run"
# 	python test.py --automate
# 	python test.py --notify