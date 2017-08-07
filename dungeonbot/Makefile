migrate:
	./manage.py makemigrations && ./manage.py migrate

test: migrate
	coverage run --source='.' manage.py test
	coverage report -m

verbose-test: migrate
	coverage run --source='.' manage.py test -v 3
	coverage report -m

.PHONY: migrate test verbose-test
