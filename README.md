# CV as Code

Source-controlled CV workflow for Sebastian Mendel.

Published version:

<https://cybottm.github.io/cv/>

## Files

| Path | Purpose |
|---|---|
| `src/cv-executive.de.md` | Short public executive CV |
| `src/cv-technical.de.md` | More detailed public technical CV |
| `public/index.html` | GitHub Pages entry point |
| `public/cv-executive.de.html` | Generated executive HTML CV |
| `public/cv-executive.de.pdf` | Generated executive PDF CV |
| `public/cv-technical.de.html` | Generated technical HTML CV |
| `public/cv-technical.de.pdf` | Generated technical PDF CV |
| `assets/style.css` | Shared print-friendly stylesheet |
| `Makefile` | Local build commands |

## Build

Requirements:

- `make`
- `pandoc`
- `weasyprint`

Build all generated files:

```bash
make build
```

Check that generated files are up to date:

```bash
make check
```

Remove generated HTML/PDF files:

```bash
make clean
```

## Source of truth

The Markdown files in `src/` are the source of truth. Files in `public/` are generated artifacts for GitHub Pages and downloadable HTML/PDF versions.

## Publishing

GitHub Pages serves the generated files from `public/`. The default published CV is `public/index.html`.
