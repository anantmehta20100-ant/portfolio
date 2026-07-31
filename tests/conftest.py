from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest

from app import create_app

ROOT = Path(__file__).parents[1]
STATIC = ROOT / "app" / "static"

# One declaration of the site's public pages; REQUIRED_ROUTES derives from it so
# the two can never disagree. The sitemap's own list in app/routes/main.py stays
# independent on purpose, or test_discovery's comparison would be tautological.
EXPECTED_PAGE_THEMES = {
    "/": "theme-dark",
    "/projects": "theme-dark",
    "/projects/tracksense": "theme-editorial",
    "/projects/forebid": "theme-editorial",
    "/projects/engram-pipeline": "theme-editorial",
    "/experience": "theme-dark",
    "/experience/engram": "theme-editorial",
    "/research": "theme-editorial",
    "/about": "theme-editorial",
    "/contact": "theme-editorial",
}
REQUIRED_ROUTES = tuple(EXPECTED_PAGE_THEMES)

VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class DomNode:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.children = []

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    @property
    def text(self):
        parts = []
        for child in self.children:
            parts.append(child.text if isinstance(child, DomNode) else child)
        return " ".join(" ".join(parts).split())

    def find_all(self, tag=None, **attributes):
        matches = []
        for child in self.children:
            if not isinstance(child, DomNode):
                continue
            if child.matches(tag, attributes):
                matches.append(child)
            matches.extend(child.find_all(tag, **attributes))
        return matches

    def find_one(self, tag=None, **attributes):
        matches = self.find_all(tag, **attributes)
        assert len(matches) == 1, (
            f"Expected one {tag or 'element'} matching {attributes}, "
            f"found {len(matches)}"
        )
        return matches[0]

    def matches(self, tag, attributes):
        if tag is not None:
            if callable(tag):
                if not tag(self.tag):
                    return False
            elif self.tag != tag:
                return False
        for name, expected in attributes.items():
            name = "class" if name == "class_" else name
            actual = self.attrs.get(name)
            if name == "class":
                if expected not in self.classes:
                    return False
            elif callable(expected):
                if not expected(actual):
                    return False
            elif actual != expected:
                return False
        return True


class DomParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = DomNode("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = DomNode(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_document(html):
    parser = DomParser()
    parser.feed(html)
    parser.close()
    return parser.root


def without_version(url):
    # Static URLs carry a per-file ?v= cache-busting token. Assertions pin the
    # asset's identity, so the token is stripped before comparing.
    split = urlsplit(url)
    query = "&".join(
        part
        for part in split.query.split("&")
        if part and not part.startswith("v=")
    )
    return urlunsplit(split._replace(query=query))


def section_with_heading(document, heading):
    matches = [
        section
        for section in document.find_all("section")
        if any(node.text == heading for node in section.find_all("h2"))
    ]
    assert len(matches) == 1, (
        f"Expected one section headed {heading!r}, found {len(matches)}"
    )
    return matches[0]


@pytest.fixture()
def app():
    application = create_app({"TESTING": True})
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def parse_html():
    return parse_document
