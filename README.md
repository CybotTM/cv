# CV as Code

Source-controlled CV workflow for Sebastian Mendel.

Published version: <https://cybottm.github.io/cv/>

## Layout

| Path | Purpose |
|---|---|
| `src/cv-executive.de.md` | Source: short executive CV (Markdown + YAML front-matter) |
| `src/cv-technical.de.md` | Source: longer technical CV |
| `templates/base.html.j2` | Jinja2 base template (`<head>`, OG, JSON-LD, etc.) |
| `templates/cv.html.j2` | CV page template |
| `templates/index.html.j2` | Landing page template |
| `assets/style.css` | Editorial CSS (screen + print) |
| `assets/fonts/*.woff2` | Self-hosted Source Serif 4 + Inter (variable, OFL) |
| `assets/favicon.svg` | Monogram favicon |
| `scripts/build.py` | The whole build: MD → HTML → PDF + index |
| `requirements.txt` | Python deps (pinned) |
| `Makefile` | Convenience targets (`build`, `serve`, `lighthouse`, `clean`) |
| `.github/workflows/build.yml` | GitHub Actions: build, Lighthouse-CI on PRs, Pages deploy |
| `public/` | **Build artifact** — generated, not committed |

## Build locally

You need Python 3.13 and the WeasyPrint runtime libs (Pango, Cairo, HarfBuzz, gdk-pixbuf).

```bash
# Debian/Ubuntu
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libcairo2 libgdk-pixbuf-2.0-0

make install   # creates .venv/ and installs requirements.txt
make build     # writes public/cv-*.de.html + .pdf and public/index.html
make serve     # builds, then serves public/ on http://localhost:8000
```

Skip PDF rendering during a fast iteration:

```bash
.venv/bin/python scripts/build.py --no-pdf
```

## Local Lighthouse audit

```bash
make lighthouse   # writes lighthouse-*.html for each page
```

## Editing content

Each `src/cv-*.de.md` has a YAML front-matter block: `variant`, `short_label`,
`lang`, `title`, `description`, `updated`, `og_locale`. The body is plain Markdown.
The `<h1>` and tagline are rendered from `templates/cv.html.j2`, not from the MD,
so the MD body should start at `## Profil`.

### Claims and sources

- Every factual claim (role, scope, period, figure) needs a source that is kept outside this repository. Look the source up before changing a claim instead of reconstructing it from memory.
- This repository is public: the CV stays anonymous about clients, colleagues and internal documents. Client names belong only in an application-specific version, after an NDA check, and never here.
- "Head of Operations" and "Teamleiter Support (Kundenprojekte)" name the same role (2011–2016); keep both labels.
- The CTO responsibility since 2015 is continuous across all three technology domains. Describe 2019–2023 as operational IT support by a Head of IT under that responsibility, and 2024 onwards as continuing without it — never as a handover and a take-back, which would read as a five-year gap.

## CI / publishing

- Every push and PR builds the site.
- PRs additionally run [`treosh/lighthouse-ci-action`](https://github.com/treosh/lighthouse-ci-action) and post results.
- Pushes to `main` deploy to GitHub Pages.

## License

CV content © Sebastian Mendel. Source code (templates, scripts, CSS) under the
repository's license; bundled fonts (Source Serif 4, Inter) under SIL OFL.
