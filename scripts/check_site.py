#!/usr/bin/env python3
"""Check built HTML without network access or third-party Python dependencies."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlparse


@dataclass
class Document:
    ids: set[str] = field(default_factory=set)
    links: list[tuple[str, str]] = field(default_factory=list)
    image_errors: list[str] = field(default_factory=list)
    title: bool = False
    language: bool = False
    h1_count: int = 0
    redirect: bool = False


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.document = Document()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        d = self.document
        if a.get("id"):
            d.ids.add(a["id"] or "")
        if tag == "html":
            d.language = bool(a.get("lang"))
        if tag == "title":
            d.title = True
        if tag == "h1":
            d.h1_count += 1
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            d.redirect = True
        if tag == "img":
            if "alt" not in a:
                d.image_errors.append(f"Image missing alt: {a.get('src')}")
            if not a.get("width") or not a.get("height"):
                d.image_errors.append(f"Image missing dimensions: {a.get('src')}")
        for attr in ("href", "src"):
            value = a.get(attr)
            if value:
                d.links.append((f"{tag}[{attr}]", value))
        if a.get("srcset"):
            for item in a["srcset"].split(","):
                value = item.strip().split(" ")[0]
                if value:
                    d.links.append(("srcset", value))


def page_url(path: Path, root: Path, base_url: str) -> str:
    relative = path.relative_to(root).as_posix()
    if relative.endswith("index.html"):
        relative = relative[:-len("index.html")]
    return urljoin(base_url.rstrip("/") + "/", relative)


def local_target(value: str, current_url: str, base_url: str, root: Path) -> tuple[Path, str] | None:
    target = urlparse(urljoin(current_url, value))
    base = urlparse(base_url)
    if target.scheme not in ("http", "https") or target.netloc != base.netloc:
        return None
    prefix = base.path.rstrip("/") + "/"
    path = unquote(target.path)
    if prefix != "/" and not path.startswith(prefix):
        raise ValueError(f"Internal URL escapes deployment prefix {prefix}: {value}")
    relative = path[len(prefix):] if path.startswith(prefix) else path.lstrip("/")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes site root: {value}")
    if path.endswith("/") or resolved.is_dir():
        resolved /= "index.html"
    elif not resolved.suffix and not resolved.exists():
        resolved /= "index.html"
    return resolved, unquote(target.fragment)


def inspect_site(root: Path, base_url: str) -> tuple[list[str], dict[str, int]]:
    root = root.resolve()
    documents: dict[Path, Document] = {}
    errors: list[str] = []
    count = 0
    for path in sorted(root.rglob("*.html")):
        parser = Inspector()
        parser.feed(path.read_text(encoding="utf-8"))
        documents[path] = parser.document
    for path, d in documents.items():
        label = path.relative_to(root).as_posix()
        if not d.redirect:
            if not d.title:
                errors.append(f"{label}: missing title")
            if not d.language:
                errors.append(f"{label}: missing document language")
            errors.extend(f"{label}: {error}" for error in d.image_errors)
            if "/_print/" not in "/" + label and d.h1_count != 1:
                errors.append(f"{label}: expected one h1; found {d.h1_count}")
        current_url = page_url(path, root, base_url)
        for kind, value in d.links:
            count += 1
            try:
                item = local_target(value, current_url, base_url, root)
            except ValueError as error:
                errors.append(f"{label}: {error}")
                continue
            if item is None:
                continue
            target, fragment = item
            if not target.is_file():
                errors.append(f"{label}: broken {kind}: {value}")
            elif fragment and not fragment.startswith(":~:text=") and target in documents:
                if fragment not in documents[target].ids:
                    errors.append(f"{label}: missing anchor {fragment}: {value}")
    # The custom site owns these assets and content destinations.
    for resource in ("index.html", "docs/index.html", "blog/index.html", "llms.txt", "navigation.json", "images/architecture.svg"):
        if not (root / resource).is_file():
            errors.append(f"Required output missing: {resource}")
    return sorted(set(errors)), {"html_pages": len(documents), "references_checked": count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--base-url", default="http://localhost:1313/")
    args = parser.parse_args()
    errors, stats = inspect_site(args.directory, args.base_url)
    for error in errors:
        print("FAIL", error)
    print(f"Checked {stats['html_pages']} HTML pages and {stats['references_checked']} references; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
