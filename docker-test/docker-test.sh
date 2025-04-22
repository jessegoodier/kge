#!/bin/bash

python3 -m venv /tmp/venv
source /tmp/venv/bin/activate
pip install poetry
poetry install
poetry check
poetry run pytest
