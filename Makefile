PYTHON ?= python3
VENV   ?= .venv

.PHONY: help build serve clean install lighthouse

help:
	@echo "make install    - create venv and install dependencies"
	@echo "make build      - build public/ from src/ (HTML + PDF)"
	@echo "make serve      - build and serve public/ on http://localhost:8000"
	@echo "make lighthouse - run a local Lighthouse audit (needs npx)"
	@echo "make clean      - remove public/ and venv"

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV) || (which uv && uv venv $(VENV))
	$(VENV)/bin/python -m pip install -U pip || $(VENV)/bin/python -m ensurepip --upgrade
	$(VENV)/bin/python -m pip install -r requirements.txt

install: $(VENV)/bin/python

build: install
	$(VENV)/bin/python scripts/build.py

serve: build
	@echo "Serving public/ on http://localhost:8000"
	$(PYTHON) -m http.server 8000 -d public

lighthouse: build
	@echo "Running Lighthouse on built public/"
	npx --yes lighthouse "file://$(CURDIR)/public/index.html" \
	  --quiet --chrome-flags="--headless" \
	  --output html --output-path ./lighthouse-index.html
	npx --yes lighthouse "file://$(CURDIR)/public/cv-executive.de.html" \
	  --quiet --chrome-flags="--headless" \
	  --output html --output-path ./lighthouse-executive.html
	npx --yes lighthouse "file://$(CURDIR)/public/cv-technical.de.html" \
	  --quiet --chrome-flags="--headless" \
	  --output html --output-path ./lighthouse-technical.html

clean:
	rm -rf public $(VENV) lighthouse-*.html
