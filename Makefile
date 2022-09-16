# -*- mode: makefile -*-
# Copyright 2022 Meta Mind AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

PYTHON_VERSION=$(shell cat .python-version)
export TAXONOMY_JSON_FILE_DATA_SOURCES=data/

.PHONY: test
test: test/pytest test/typing test/style test/jsonschema test/integration

.PHONY: test/pytest
test/pytest:
	pipenv run pytest --doctest-modules

.PHONY: test/typing
test/typing:
	pipenv run mypy application.py

.PHONY: test/style
test/style:
	pipenv run pycodestyle --max-line-length=88 application.py

.PHONY: test/jsonschema
test/jsonschema:
	for i in $$(find ${TAXONOMY_JSON_FILE_DATA_SOURCES} -name '*.json'); do pipenv run jsonschema taxonomy/schema.json --i $$i || exit 1; done

.PHONY: test/integration
test/integration:
	pipenv run ./runintegrationtests.sh


.PHONY: dev-setup
dev-setup:
	@pyenv local ${PYTHON_VERSION} || (echo "Please run: pyenv install ${PYTHON_VERSION}" && false)
	pipenv --python=$$(pyenv which python) sync --dev

.PHONY: clean
clean:
	find . -name __pycache__ -exec rm -rf {} \;

.PHONY: up
up:
	pipenv run python application.py


.PHONY: build/docker
build/docker:
	docker-compose --project-dir  . -f docker/docker-compose.yml build --build-arg PYTHON_VERSION=${PYTHON_VERSION}

.PHONY: up/docker
up/docker: build/docker
	docker-compose --project-dir . -f docker/docker-compose.yml -f docker/docker-compose.local.yml up --no-build
