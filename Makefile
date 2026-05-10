PANDOC ?= pandoc
WEASYPRINT ?= weasyprint
CSS := assets/style.css
PUBLIC := public
SRC := src

EXEC_MD := $(SRC)/cv-executive.de.md
TECH_MD := $(SRC)/cv-technical.de.md

EXEC_HTML := $(PUBLIC)/cv-executive.de.html
TECH_HTML := $(PUBLIC)/cv-technical.de.html
EXEC_PDF := $(PUBLIC)/cv-executive.de.pdf
TECH_PDF := $(PUBLIC)/cv-technical.de.pdf
INDEX_HTML := $(PUBLIC)/index.html

.PHONY: build html pdf index check clean

build: html pdf index
html: $(EXEC_HTML) $(TECH_HTML)
pdf: $(EXEC_PDF) $(TECH_PDF)
index: $(INDEX_HTML)

$(PUBLIC):
	mkdir -p $(PUBLIC)

$(EXEC_HTML): $(EXEC_MD) $(CSS) | $(PUBLIC)
	@if command -v $(PANDOC) >/dev/null 2>&1; then \
		$(PANDOC) $< -f markdown -t html5 --standalone --metadata title="Executive CV" --metadata lang="de" --css=../$(CSS) -o $@; \
	else \
		python3 scripts/render_html.py $< $@ ../$(CSS); \
	fi

$(TECH_HTML): $(TECH_MD) $(CSS) | $(PUBLIC)
	@if command -v $(PANDOC) >/dev/null 2>&1; then \
		$(PANDOC) $< -f markdown -t html5 --standalone --metadata title="Technical CV" --metadata lang="de" --css=../$(CSS) -o $@; \
	else \
		python3 scripts/render_html.py $< $@ ../$(CSS); \
	fi

$(EXEC_PDF): $(EXEC_HTML) $(CSS)
	@if command -v $(WEASYPRINT) >/dev/null 2>&1; then \
		$(WEASYPRINT) $< $@; \
	else \
		python3 scripts/render_pdf.py $< $@; \
	fi

$(TECH_PDF): $(TECH_HTML) $(CSS)
	@if command -v $(WEASYPRINT) >/dev/null 2>&1; then \
		$(WEASYPRINT) $< $@; \
	else \
		python3 scripts/render_pdf.py $< $@; \
	fi

$(INDEX_HTML): $(EXEC_HTML)
	cp $(EXEC_HTML) $(INDEX_HTML)

check: build
	git diff --exit-code public/

clean:
	rm -f $(EXEC_HTML) $(TECH_HTML) $(EXEC_PDF) $(TECH_PDF) $(INDEX_HTML)
