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

PERSON_ID = f"{SITE_BASE}/#person"
WEBSITE_ID = f"{SITE_BASE}/#website"

PERSON_JSONLD = {
    "@type": "Person",
    "@id": PERSON_ID,
    "name": AUTHOR["name"],
    "givenName": AUTHOR["first_name"],
    "familyName": AUTHOR["last_name"],
    "jobTitle": AUTHOR["role"],
    "description": (
        "Chief Technology Officer und Senior Engineering Leader mit über 25 "
        "Jahren IT-Erfahrung. Verbindet technische Strategie und "
        "Engineering-Governance mit operativer Plattformarbeit, "
        "Modernisierung komplexer Systemlandschaften und der Einführung "
        "AI-gestützter Engineering-Praktiken. Maintainer mehrerer "
        "Open-Source-Projekte, Initiator des internen RFC-Prozesses und "
        "des unternehmensweiten Trainingsprogramms für agentische "
        "Entwicklung."
    ),
    "url": f"{SITE_BASE}/",
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Leipzig",
        "postalCode": "04229",
        "addressCountry": "DE",
    },
    "worksFor": {
        "@type": "Organization",
        "name": "Netresearch DTT GmbH",
        "url": "https://www.netresearch.de/",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Nonnenstraße 11d",
            "postalCode": "04229",
            "addressLocality": "Leipzig",
            "addressCountry": "DE",
        },
    },
    "alumniOf": [
        {
            "@type": "EducationalOrganization",
            "name": "Staatliche Berufsschule Erlangen",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Erlangen",
                "addressCountry": "DE",
            },
        },
    ],
    "knowsLanguage": [
        {"@type": "Language", "name": "Deutsch", "alternateName": "de"},
        {"@type": "Language", "name": "Englisch", "alternateName": "en"},
    ],
    "knowsAbout": [
        # Leadership & methodology
        "Engineering Leadership",
        "Engineering Governance",
        "Technical Strategy",
        "Architecture Decision Records",
        "RFC Process",
        "Curriculum Design",
        "Mentoring and Coaching",
        "Organizational Change Management",
        "Stakeholder Communication",
        "Presales and Technical Advisory",
        # Architecture
        "Platform Architecture",
        "Technical Modernization",
        "API Design",
        "Distributed Systems",
        # AI-era engineering
        "AI-assisted Engineering",
        "Agentic Development",
        "Prompt Engineering",
        "Model Context Protocol",
        "Skill Marketplace Engineering",
        # Security & compliance
        "Information Security",
        "ISO/IEC 27001-aligned ISMS Documentation",
        "BSI IT-Grundschutz",
        "Cloud Compliance (BSI C5)",
        "Disaster Recovery",
        "Business Continuity",
        "Supply-Chain Security",
        # Operations & platforms
        "Continuous Integration",
        "Continuous Delivery",
        "DevOps",
        "Job Scheduling",
        "Cron and DAG-based Workflow Engines",
        "Identity and Access Management",
        "LDAP and Active Directory",
        "Reverse Proxy Architecture (Traefik)",
        "Matrix / Synapse Operations",
        "Composer Registry Operations",
        "Open Source Maintainership",
        # Stack
        "TYPO3",
        "Magento",
        "OroCommerce",
        "Shopware",
        "Akeneo",
        "PHP",
        "Go",
        "Python",
        "TypeScript",
        "JavaScript",
        "Bash",
        "SQL",
        "Linux",
        "Docker",
        "GitLab",
        "Concourse CI",
        "Proxmox",
        "AWS",
    ],
    "hasOccupation": {
        "@type": "Occupation",
        "name": "Chief Technology Officer",
        "occupationLocation": {"@type": "City", "name": "Leipzig"},
        "experienceRequirements": "25+ years IT, 10+ years CTO",
        "skills": (
            "Technical strategy and engineering governance, "
            "platform architecture and modernization of complex system "
            "landscapes, information security and compliance "
            "documentation (BSI IT-Grundschutz, BSI C5, ISMS), "
            "AI-assisted and agentic engineering practices, "
            "open-source maintainership, curriculum design and "
            "mentoring, cross-functional stakeholder communication, "
            "organizational change management."
        ),
    },
    "sameAs": [AUTHOR["linkedin"], AUTHOR["github"]],
}

WEBSITE_JSONLD = {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    "url": f"{SITE_BASE}/",
    "name": f"{AUTHOR['name']} — Curriculum Vitae",
    "inLanguage": "de",
    "publisher": {"@id": PERSON_ID},
}


def page_jsonld(page_id: str, url: str, name: str, lang: str, updated_iso: str,
                breadcrumb: dict | None = None) -> dict:
    """Build a `@graph` JSON-LD payload for a single page.

    Each page gets a ProfilePage node referencing the shared Person and
    WebSite by `@id`. CV variant pages also get a BreadcrumbList. The
    schema.org/ProfilePage type is the canonical type for personal-profile
    pages and is supported by Google rich results since 2023.
    """
    profile = {
        "@type": "ProfilePage",
        "@id": page_id,
        "url": url,
        "name": name,
        "inLanguage": lang,
        "dateModified": updated_iso,
        "isPartOf": {"@id": WEBSITE_ID},
        "about": {"@id": PERSON_ID},
        "mainEntity": {"@id": PERSON_ID},
    }
    if breadcrumb is not None:
        profile["breadcrumb"] = {"@id": breadcrumb["@id"]}

    graph = [profile, PERSON_JSONLD, WEBSITE_JSONLD]
    if breadcrumb is not None:
        graph.append(breadcrumb)
    return {"@context": "https://schema.org", "@graph": graph}


def variant_breadcrumb(variant: "Variant") -> dict:
    return {
        "@type": "BreadcrumbList",
        "@id": f"{variant.canonical}#breadcrumb",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Übersicht",
                "item": f"{SITE_BASE}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": variant.front["short_label"] + " CV",
                "item": variant.canonical,
            },
        ],
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
    # `abbr` extension wraps every occurrence of a defined token in
    # <abbr title="…"> — WCAG 3.1.4 AAA Abbreviations.
    md = markdown.Markdown(
        extensions=["extra", "smarty", "sane_lists", "attr_list", "abbr"],
        output_format="html5",
    )
    return md.convert(body)


def load_abbreviations() -> str:
    """Return the contents of `src/_abbreviations.md` (or '' if absent).

    The block uses Markdown's `abbr` extension syntax: each line is
    `*[KEY]: Expansion`. We append it to every CV body before rendering so
    every occurrence of KEY in the body becomes <abbr title="Expansion">KEY</abbr>.
    """
    path = SRC / "_abbreviations.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
    abbr_block: str = "",
) -> str:
    tpl = env.get_template("cv.html.j2")
    breadcrumb = variant_breadcrumb(variant)
    jsonld = page_jsonld(
        page_id=f"{variant.canonical}#profilepage",
        url=variant.canonical,
        name=variant.front["title"],
        lang=variant.front["lang"],
        updated_iso=build_iso,
        breadcrumb=breadcrumb,
    )
    body_md_with_abbr = variant.body_md + "\n\n" + abbr_block
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
        jsonld=json.dumps(jsonld, ensure_ascii=False),
        body=render_md(body_md_with_abbr),
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
    title = f"{AUTHOR['name']} — Curriculum Vitae"
    jsonld = page_jsonld(
        page_id=f"{canonical}#profilepage",
        url=canonical,
        name=title,
        lang="de",
        updated_iso=build_iso,
    )
    return tpl.render(
        lang="de",
        title=title,
        description=(
            f"{AUTHOR['name']}, {AUTHOR['role']} in {AUTHOR['location']}. "
            "Lebenslauf in zwei Varianten: Executive (kurz, leitungsorientiert) "
            "und Technical (detailliert, technologiefokussiert)."
        ),
        canonical=canonical,
        og_locale="de_DE",
        author=AUTHOR,
        jsonld=json.dumps(jsonld, ensure_ascii=False),
        lede=(
            f"{AUTHOR['role']} bei Netresearch DTT GmbH, Leipzig. "
            "Über 25 Jahre IT-Erfahrung mit Schwerpunkt auf Engineering-Governance, "
            "Plattformarchitektur und Modernisierung komplexer Systemlandschaften."
        ),
        mantra=(
            "Mein Fokus liegt auf langlebigen technischen Strukturen: "
            "Wissen aus Silos holen, Komplexität erklärbar machen und "
            "Teams so befähigen, dass Systeme nicht von einzelnen "
            "Schlüsselpersonen abhängen."
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

    # ISO 8601 datetime with explicit UTC offset — required for schema.org
    # dateModified validation (date-only "YYYY-MM-DD" gets flagged).
    now = datetime.now(timezone.utc).replace(microsecond=0)
    build_iso = now.isoformat()
    inline_css = load_inline_css()
    abbr_block = load_abbreviations()

    for v in variants:
        html = render_html(env, v, variants, build_iso, inline_css, abbr_block)
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
