# CV as Code

This repository contains a source-controlled CV workflow.

## Principles

- Markdown files in `src/` are the source of truth.
- Public HTML/PDF files in `public/` are generated artifacts.
- Private/source-detailed content remains separated from public variants.

## Build requirements

- `pandoc`
- `weasyprint`
- `make`

## Commands

```bash
make build
make clean
```

## Important files

- `src/cv-full.private.md`: private/full CV source
- `src/cv-executive.de.md`: public executive CV (German)
- `src/cv-technical.de.md`: public technical CV (German)
- `assets/style.css`: shared stylesheet for generated HTML
- `Makefile`: reproducible local build pipeline
- `.github/workflows/build.yml`: CI build/check and GitHub Pages deployment
- `public/`: generated public HTML/PDF outputs
