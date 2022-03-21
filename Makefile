check:
	@[ -f ".env" ] || (echo "Missing .env file" && false)
	@python manage.py check_configuration

deps:
	pip install -r requirements.txt
	rm -f package-lock.json && yarn install

venv:
	@echo 'You must run: . venv/bin/activate'

crypt-key:
	python manage.py generate_crypt_key

demo-uuid:
	python manage.py generate_demo_uuid

shell:
	python manage.py shell

run:
	python manage.py runserver -h 0.0.0.0 -p 8080

test: check
	py.test -s -vv app/

css:
	npm run css

locales:
	bin/build-locales

build: locales

routes:
	python manage.py list_routes

load-clerks:
	python manage.py load_clerks

load-demo:
	python manage.py load_demo

load-zipcodes:
	python manage.py load_zipcodes

fixtures: load-clerks load-demo load-zipcodes

deploy-prod:
	git push production master

deploy-stage-fixtures:
	heroku run 'make fixtures' --app ksvotes-staging

deploy-prod-fixtures:
	heroku run 'make fixtures' --app ksvotes-production

redact:
	python manage.py redact_pii

export:
	python manage.py export_registrants

start-services:
	docker-compose up -d

stop-services:
	docker-compose down

.PHONY: deps venv test run fixtures redact export start-services stop-services
