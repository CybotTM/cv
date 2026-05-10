#!/usr/bin/env python3
"""Build the static CV site from Markdown sources.

Reads `src/cv-*.de.md` (each with YAML front-matter), renders them through
Jinja2 templates, writes self-contained HTML to `public/`, and emits matching
PDF files via WeasyPrint. Also writes a landing `public/index.html`.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "templates"
PUBLIC = ROOT / "public"

SITE_BASE = "https://cybottm.github.io/cv"

AUTHOR = {
    "name": "Sebastian Mendel",
    "first_name": "Sebastian",
    "last_name": "Mendel",
    "role": "Chief Technology Officer",
    "location": "Leipzig, Deutschland",
    "linkedin": "https://linkedin.com/in/sebastian-mendel",
    "github": "https://github.com/CybotTM",
}

JSONLD = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": AUTHOR["name"],
    "givenName": AUTHOR["first_name"],
    "familyName": AUTHOR["last_name"],
    "jobTitle": AUTHOR["role"],
    "address": {"@type": "PostalAddress", "addressLocality": "Leipzig", "addressCountry": "DE"},
    "worksFor": {
        "@type": "Organization",
        "name": "Netresearch DTT GmbH",
        "url": "https://www.netresearch.de/",
    },
    "url": f"{SITE_BASE}/",
    "sameAs": [AUTHOR["linkedin"], AUTHOR["github"]],
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class Variant:
    """A single CV variant rendered from one Markdown source file."""

    slug: str  # e.g. "cv-executive.de"
    front: dict
    body_md: str

    @property
    def html_filename(self) -> str:
        return f"{self.slug}.html"

    @property
    def pdf_filename(self) -> str:
        return f"{self.slug}.pdf"

    @property
    def canonical(self) -> str:
        return f"{SITE_BASE}/{self.html_filename}"


def parse_source(path: Path) -> Variant:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SystemExit(f"{path}: missing YAML front-matter (--- ... ---)")
    front = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    slug = path.name.removesuffix(".md")
    return Variant(slug=slug, front=front, body_md=body)


def render_md(body: str) -> str:
    md = markdown.Markdown(
        extensions=["extra", "smarty", "sane_lists", "attr_list"],
        output_format="html5",
    )
    return md.convert(body)


def load_inline_css() -> str:
    """Load assets/style.css and rewrite font URLs for inlining into HTML.

    The source CSS sits at assets/style.css and references fonts as
    `url("fonts/...")` (relative to the CSS). When the same CSS is inlined
    into a `<style>` element in an HTML file at the public/ root, the
    browser resolves URLs relative to the *HTML*, so the references must
    become `url("assets/fonts/...")`. This matches what the
    `<link rel=preload as=font href="assets/fonts/...">` hints already use,
    so the preload is reused for the @font-face request.
    """
    css = (ASSETS / "style.css").read_text(encoding="utf-8")
    return re.sub(r'url\((\s*"?)fonts/', r'url(\1assets/fonts/', css)


def build_meta_links(variant: Variant, all_variants: list[Variant]) -> list[dict]:
    """Header navigation: external profiles + alternate CV variants/PDFs."""
    links: list[dict] = [
        {"href": "index.html", "text": "Übersicht"},
        {"href": AUTHOR["linkedin"], "text": "LinkedIn", "rel": "me"},
        {"href": AUTHOR["github"], "text": "GitHub", "rel": "me"},
    ]
    for v in all_variants:
        is_current = v.slug == variant.slug
        label = v.front["short_label"]
        links.append(
            {
                "href": v.html_filename,
                "text": f"{label} (HTML)",
                "current": is_current,
            }
        )
        links.append(
            {
                "href": v.pdf_filename,
                "text": f"{label} (PDF)",
                "aria": f"{v.front['title']} als PDF herunterladen",
            }
        )
    return links


def render_html(
    env: Environment,
    variant: Variant,
    all_variants: list[Variant],
    build_iso: str,
    inline_css: str,
) -> str:
    tpl = env.get_template("cv.html.j2")
    # Asset paths are relative to the HTML file. Both index.html and cv-*.de.html
    # sit at the root of public/ alongside assets/, so plain "assets/..." works
    # for every page; "../assets/..." would escape the project subpath on Pages.
    return tpl.render(
        variant=variant.front["variant"],
        lang=variant.front["lang"],
        title=variant.front["title"],
        description=variant.front["description"],
        canonical=variant.canonical,
        og_locale=variant.front.get("og_locale", "de_DE"),
        author=AUTHOR,
        jsonld=json.dumps(JSONLD, ensure_ascii=False),
        body=render_md(variant.body_md),
        pdf_filename=variant.pdf_filename,
        meta_links=build_meta_links(variant, all_variants),
        updated_human=variant.front["updated"],
        build_iso=build_iso,
        inline_css=inline_css,
        asset=lambda p: f"assets/{p}",
    )


def render_index(
    env: Environment,
    all_variants: list[Variant],
    build_iso: str,
    inline_css: str,
) -> str:
    tpl = env.get_template("index.html.j2")
    canonical = f"{SITE_BASE}/"
    return tpl.render(
        lang="de",
        title=f"{AUTHOR['name']} — Curriculum Vitae",
        description=(
            f"{AUTHOR['name']}, {AUTHOR['role']} in {AUTHOR['location']}. "
            "Lebenslauf in zwei Varianten: Executive (kurz, leitungsorientiert) "
            "und Technical (detailliert, technologiefokussiert)."
        ),
        canonical=canonical,
        og_locale="de_DE",
        author=AUTHOR,
        jsonld=json.dumps(JSONLD, ensure_ascii=False),
        lede=(
            f"{AUTHOR['role']} bei Netresearch DTT GmbH, Leipzig. "
            "Über 25 Jahre IT-Erfahrung mit Schwerpunkt auf Engineering-Governance, "
            "Plattformarchitektur und Modernisierung komplexer Systemlandschaften."
        ),
        variants=[
            {
                "title": v.front["title"],
                "description": v.front["description"],
                "html": v.html_filename,
                "pdf": v.pdf_filename,
            }
            for v in all_variants
        ],
        contacts=[
            {"href": AUTHOR["linkedin"], "text": "LinkedIn"},
            {"href": AUTHOR["github"], "text": "GitHub"},
        ],
        build_iso=build_iso,
        inline_css=inline_css,
        pdf_filename=None,
        asset=lambda p: f"assets/{p}",
    )


def write_pdf(html_path: Path, pdf_path: Path) -> None:
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF rendering")
    args = parser.parse_args()

    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)

    shutil.copytree(ASSETS, PUBLIC / "assets")

    favicon = ASSETS / "favicon.svg"
    if favicon.exists():
        shutil.copy2(favicon, PUBLIC / "favicon.svg")

    sources = sorted(SRC.glob("cv-*.de.md"))
    if not sources:
        raise SystemExit(f"No CV sources found under {SRC}")
    variants = [parse_source(p) for p in sources]

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    build_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    inline_css = load_inline_css()

    for v in variants:
        html = render_html(env, v, variants, build_iso, inline_css)
        out = PUBLIC / v.html_filename
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
        if not args.no_pdf:
            pdf_out = PUBLIC / v.pdf_filename
            write_pdf(out, pdf_out)
            print(f"wrote {pdf_out.relative_to(ROOT)} ({pdf_out.stat().st_size // 1024} KB)")

    index_html = render_index(env, variants, build_iso, inline_css)
    (PUBLIC / "index.html").write_text(index_html, encoding="utf-8")
    print(f"wrote public/index.html")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
