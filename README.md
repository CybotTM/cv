# Lebenslauf — Sebastian Mendel

Lebenslauf von Sebastian Mendel, CTO bei [Netresearch DTT GmbH](https://www.netresearch.de/), Leipzig.

## Inhalt

- [`lebenslauf-sebastian-mendel.md`](./lebenslauf-sebastian-mendel.md) — Lebenslauf in Markdown (Quelle)
- [`lebenslauf-sebastian-mendel.html`](./lebenslauf-sebastian-mendel.html) — gerenderte HTML-Fassung
- [`style.css`](./style.css) — Stylesheet (Netresearch-Brand-Farben, druckoptimiert)

## Rendern

```bash
pandoc lebenslauf-sebastian-mendel.md \
  -f markdown -t html5 \
  --standalone \
  --metadata title="Sebastian Mendel — Lebenslauf" \
  --metadata lang="de" \
  --css=style.css \
  -o lebenslauf-sebastian-mendel.html
```

## Kontakt

GitHub: [@CybotTM](https://github.com/CybotTM)
