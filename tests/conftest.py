from html.parser import HTMLParser

import pytest

from app import create_app

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
