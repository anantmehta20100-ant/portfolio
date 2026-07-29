import importlib
import json
from urllib.parse import urlsplit
from xml.etree import ElementTree

import pytest

from app import create_app


REQUIRED_ROUTES = (
    "/",
    "/projects",
    "/projects/tracksense",
    "/projects/forebid",
    "/projects/engram-pipeline",
    "/experience",
    "/experience/engram",
    "/research",
    "/about",
    "/contact",
)


def metadata_content(document, property_name):
    return document.find_one("meta", property=property_name).attrs["content"]


def test_robots_allows_public_crawling(client):
    response = client.get("/robots.txt")
    assert response.mimetype == "text/plain"
    assert "User-agent: *" in response.get_data(as_text=True)
    assert "Sitemap:" in response.get_data(as_text=True)


def test_sitemap_contains_each_required_route_exactly_once(client):
    response = client.get("/sitemap.xml")
    root = ElementTree.fromstring(response.get_data(as_text=True))
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [
        node.text for node in root.findall("sitemap:url/sitemap:loc", namespace)
    ]

    assert response.mimetype == "application/xml"
    assert locations == [f"http://localhost{path}" for path in REQUIRED_ROUTES]
    assert len(locations) == len(set(locations))


def test_robots_uses_configured_canonical_sitemap_url():
    app = create_app(
        {
            "TESTING": True,
            "CANONICAL_BASE_URL": "https://portfolio.example/",
        }
    )

    response = app.test_client().get("/robots.txt", headers={"Host": "preview.example"})

    assert "Sitemap: https://portfolio.example/sitemap.xml" in response.get_data(
        as_text=True
    )


def test_sitemap_normalizes_configured_canonical_base_url():
    app = create_app(
        {
            "TESTING": True,
            "CANONICAL_BASE_URL": "https://portfolio.example/",
        }
    )

    response = app.test_client().get("/sitemap.xml", headers={"Host": "preview.example"})
    xml = response.get_data(as_text=True)

    assert response.mimetype == "application/xml"
    assert "<loc>https://portfolio.example/projects</loc>" in xml
    assert "portfolio.example//projects" not in xml


def test_required_pages_have_complete_canonical_and_open_graph_metadata(
    parse_html,
):
    app = create_app(
        {
            "TESTING": True,
            "CANONICAL_BASE_URL": "https://portfolio.example/",
        }
    )
    client = app.test_client()
    canonicals = set()
    open_graph_titles = set()
    open_graph_descriptions = set()

    for path in REQUIRED_ROUTES:
        document = parse_html(
            client.get(path, headers={"Host": "preview.example"}).get_data(
                as_text=True
            )
        )
        head = document.find_one("head")
        title = head.find_one("title").text
        description = head.find_one("meta", name="description").attrs["content"]
        canonical = head.find_one("link", rel="canonical").attrs["href"]
        expected_canonical = f"https://portfolio.example{path}"

        assert canonical == expected_canonical
        assert metadata_content(document, "og:type") == "website"
        assert metadata_content(document, "og:title") == title
        assert metadata_content(document, "og:description") == description
        assert metadata_content(document, "og:url") == canonical
        assert metadata_content(document, "og:image").endswith(
            "/static/images/brand/social-preview-placeholder.svg"
        )
        assert metadata_content(document, "og:image:alt") == (
            "Anant Nitai Mehta — practical systems in AI and robotics"
        )
        assert canonical not in canonicals
        assert title not in open_graph_titles
        assert description not in open_graph_descriptions
        canonicals.add(canonical)
        open_graph_titles.add(title)
        open_graph_descriptions.add(description)


def test_social_preview_uses_configured_canonical_origin(parse_html):
    app = create_app(
        {
            "TESTING": True,
            "CANONICAL_BASE_URL": "https://portfolio.example/",
        }
    )
    document = parse_html(
        app.test_client()
        .get("/", headers={"Host": "preview.example"})
        .get_data(as_text=True)
    )

    assert metadata_content(document, "og:image") == (
        "https://portfolio.example/static/images/brand/"
        "social-preview-placeholder.svg"
    )


def test_wsgi_loads_canonical_origin_from_environment(
    monkeypatch,
    parse_html,
):
    monkeypatch.setenv("CANONICAL_BASE_URL", " https://portfolio.example/ ")
    production_wsgi = importlib.import_module("wsgi")
    production_wsgi = importlib.reload(production_wsgi)
    client = production_wsgi.app.test_client()

    document = parse_html(
        client.get(
            "/projects?utm_source=review",
            headers={"Host": "untrusted-preview.example"},
        ).get_data(as_text=True)
    )

    assert production_wsgi.app.config["CANONICAL_BASE_URL"] == (
        "https://portfolio.example"
    )
    assert document.find_one("link", rel="canonical").attrs["href"] == (
        "https://portfolio.example/projects"
    )
    assert metadata_content(document, "og:url") == (
        "https://portfolio.example/projects"
    )
    assert metadata_content(document, "og:image") == (
        "https://portfolio.example/static/images/brand/"
        "social-preview-placeholder.svg"
    )
    robots = client.get(
        "/robots.txt",
        headers={"Host": "untrusted-preview.example"},
    ).get_data(as_text=True)
    sitemap = client.get(
        "/sitemap.xml",
        headers={"Host": "untrusted-preview.example"},
    ).get_data(as_text=True)
    assert "Sitemap: https://portfolio.example/sitemap.xml" in robots
    assert "<loc>https://portfolio.example/projects</loc>" in sitemap
    assert "untrusted-preview.example" not in robots + sitemap


def test_explicit_canonical_config_overrides_environment(monkeypatch):
    monkeypatch.setenv("CANONICAL_BASE_URL", "https://production.example")

    app = create_app(
        {
            "TESTING": True,
            "CANONICAL_BASE_URL": "https://preview.example/",
        }
    )

    assert app.config["CANONICAL_BASE_URL"] == "https://preview.example"


def test_fallback_canonical_drops_tracking_query(parse_html):
    app = create_app({"TESTING": True, "CANONICAL_BASE_URL": ""})
    document = parse_html(
        app.test_client()
        .get(
            "/about?utm_source=review",
            headers={"Host": "preview.example"},
        )
        .get_data(as_text=True)
    )

    assert document.find_one("link", rel="canonical").attrs["href"] == (
        "http://preview.example/about"
    )
    assert metadata_content(document, "og:url") == "http://preview.example/about"
    assert metadata_content(document, "og:image").startswith(
        "http://preview.example/static/"
    )


@pytest.mark.parametrize(
    "invalid_origin",
    [
        "portfolio.example",
        "ftp://portfolio.example",
        "https://portfolio.example/path",
    ],
)
def test_invalid_canonical_environment_fails_fast(monkeypatch, invalid_origin):
    monkeypatch.setenv("CANONICAL_BASE_URL", invalid_origin)

    with pytest.raises(ValueError, match="CANONICAL_BASE_URL"):
        create_app()


def test_social_preview_and_favicon_assets_resolve(client, parse_html):
    document = parse_html(client.get("/").get_data(as_text=True))
    social_image = metadata_content(document, "og:image")
    favicon = document.find_one("link", rel="icon").attrs["href"]

    assert social_image == (
        "http://localhost/static/images/brand/social-preview-placeholder.svg"
    )
    social_response = client.get(urlsplit(social_image).path)
    favicon_response = client.get(urlsplit(favicon).path)

    assert social_response.status_code == 200
    assert social_response.mimetype == "image/svg+xml"
    assert favicon_response.status_code == 200
    assert favicon_response.mimetype == "image/svg+xml"


def test_structured_person_data_contains_only_confirmed_public_fields(
    client, parse_html
):
    document = parse_html(client.get("/").get_data(as_text=True))
    scripts = [
        script
        for script in document.find_all("script", type="application/ld+json")
    ]

    assert len(scripts) == 1
    assert json.loads(scripts[0].text) == {
        "@context": "https://schema.org",
        "@type": "Person",
        "homeLocation": "Mumbai, India",
        "name": "Anant Nitai Mehta",
        "sameAs": ["https://github.com/anantmehta20100-ant"],
        "url": "http://localhost/",
    }


def test_required_pages_do_not_link_missing_local_assets_or_routes(
    client, parse_html
):
    checked_assets = set()
    checked_routes = set()

    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        asset_urls = [
            node.attrs[attribute]
            for tag, attribute in [
                ("link", "href"),
                ("script", "src"),
                ("img", "src"),
                ("source", "src"),
            ]
            for node in document.find_all(tag)
            if node.attrs.get(attribute, "").startswith("/static/")
        ]
        for asset_url in asset_urls:
            asset_path = urlsplit(asset_url).path
            if asset_path not in checked_assets:
                assert client.get(asset_path).status_code == 200
                checked_assets.add(asset_path)

        for anchor in document.find_all("a"):
            href = anchor.attrs.get("href", "")
            parsed = urlsplit(href)
            if href.startswith("#"):
                assert document.find_one(id=parsed.fragment)
            elif href.startswith("/") and parsed.path not in checked_routes:
                assert client.get(parsed.path).status_code == 200
                checked_routes.add(parsed.path)
