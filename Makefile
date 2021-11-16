###########################
# Environment
###########################

ENV ?= $(firstword $(MAKECMDGOALS))
ifeq ($(ENV), prod)
	CLOUDBUILD = cloudbuild-prod.yml
	PROJECT_ID = darius
	APP = app-prod.yml
else
	CREDENTIAL = darius-332003-6391a8358dec.json
	CLOUDBUILD = cloudbuild-dev.yml
	PROJECT_ID = darius
	APP = app-dev.yml
	WORKER_URL = ''
endif

ifeq ($(words $(MAKECMDGOALS)), 1)
prod: build deploy
dev: build deploy
pilot: build deploy
else
dev: nan
pilot: nan
prod: nan
nan:
	@:
endif


###########################
# General
###########################

.PHONY: test
test:
	python -m pytest

style-check: flake8-check # black-check

flake8-check:
	python -m flake8

black-check:
	python -m black --line-length 188 --target-version=py37 --check ./


###########################
# Setup environment
###########################

conda-init:
	MY_SERVICE=prox3_internal
	conda create --name ${MY_SERVICE} python=3.7
	conda activate ${MY_SERVICE}
	pip install -r requirements.txt

init: create-env install version

create-env: check-env env-dependency install-env

install-env:
	@if ! [ -d $$HOME/.pyenv ]; then \
		curl https://pyenv.run | bash >/dev/null 2>&1 ; \
		if ! grep -Fq "pyenv" $$HOME/.bashrc; then\
			echo "# ===========================" >> $$HOME/.bashrc \
			echo "# Pyenv configuration        " >> $$HOME/.bashrc \
			echo "# ===========================" >> $$HOME/.bashrc \
			echo "export PATH=$$HOME/.pyenv/bin:\$$PATH" >> $$HOME/.bashrc ; \
			echo "eval \"\$$(pyenv init -)\"" >> $$HOME/.bashrc ; \
			echo "eval \"\$$(pyenv virtualenv-init -)\"" >> $$HOME/.bashrc ; \
			echo "# ===========================" >> $$HOME/.bashrc ;\
		fi \
	fi
	@. $$HOME/.bashrc
	@if ! (python3 -m pip list --disable-pip-version-check | grep pipenv > /dev/null) ; then \
		python3 -m pip install pipenv ; \
		if ! grep -Fq "\$$PATH:\$$PYTHON_BIN_PATH" $$HOME/.bashrc; then \
			echo "export PATH=\$$PATH:\$$PYTHON_BIN_PATH" >> $$HOME/.bashrc ; \
		fi \
		if ! grep -Fq "pipenv" $$HOME/.bashrc; then\
			echo "export PYTHON_BIN_PATH=$$(python3 -m site --user-base)/bin" >> $$HOME/.bashrc ; \
		fi \
	fi
	@. $$HOME/.bashrc

uninstall-env:
	python3 -m pip uninstall -y pipenv
	rm -rf $$HOME/.pyenv
	@echo "==========================="
	@echo "Need manual clean up bashrc"
	@echo "==========================="
	vim $$HOME/.bashrc

env-dependency:
	sudo apt update
	sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
	libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
	xz-utils tk-dev libffi-dev liblzma-dev python-openssl git libedit-dev

check-env:
	@if ! (python3 -m pip list --disable-pip-version-check | grep pipenv > /dev/null) ; then \
		echo "pipenv not install";\
	fi
	@if ! [ -d $$HOME/.pyenv ]; then\
		echo "pyenv not install";\
	fi
	@if ! grep -Fq "pipenv" $$HOME/.bashrc; then\
		echo "pipenv completion not in bashrc";\
	fi
	@if ! grep -Fq "pyenv" $$HOME/.bashrc; then\
		echo "pyenv not in bashrc";\
	fi
	@if ! grep -Fq "\$$PATH:\$$PYTHON_BIN_PATH" $$HOME/.bashrc; then \
		echo "pipenv PATH not in bashrc";\
	fi \

install:
	pipenv install --dev

uninstall:
	pipenv clean
	pipenv --rm

clean:
	find . -name "*.py[co]" -delete
	find . -name "*~" -delete
	find . -name "__pycache__" -delete

shell:
	pipenv shell

version:
	pipenv run python --version
	pipenv run flake8 --version
	pipenv run pytest --version


###########################
# Start at local
###########################

start-listener-local:
	python bot_listener/main.py
    
start-executor-local:
	GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIAL) project_id=$(PROJECT_ID) gunicorn bot_executor.flask_app:app \
			--bind :8000 \
			--workers 1 \
			--threads 1 \
			--timeout 900



###########################
# Build & Deploy
###########################

set-project:
	gcloud config set project $(PROJECT_ID)

build-bot-executor:
	gcloud builds submit --config bot_executor/$(CLOUDBUILD)

deploy-bot-executor:
	gcloud beta run deploy bot-executor \
			--image gcr.io/$(PROJECT_ID)/bot-executor \
			--region us-central1 \
			--platform managed \
			--cpu 1 \
			--concurrency 1 \
			--timeout 60m \
			--memory 1Gi \
			--max-instances 1 \
			--update-env-vars='project_id=$(PROJECT_ID)'