SENTRY_PATH := `python -c 'import sentry; print sentry.__file__.rsplit("/", 3)[0]'`

develop: 
	pip install "pip>=7"
	pip install -e git+https://github.com/getsentry/sentry.git#egg=sentry[dev]
	pip install -e .

install-tests: develop
	pip install .[tests]

clean:
	@echo "--> Cleaning static cache"
	rm -f src/sentry_plugins/*/static/dist
	@echo "--> Cleaning pyc files"
	find . -name "*.pyc" -delete
	@echo "--> Cleaning python build artifacts"
	rm -rf build/ dist/ src/sentry_plugins/assets.json
	@echo ""

lint: lint-python

lint-python:
	@echo "--> Linting python"
	${SENTRY_PATH}/bin/lint --python .
	@echo ""

test: install-tests
	py.test --cov=./

.PHONY: develop install-tests
