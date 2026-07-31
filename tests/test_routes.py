import re

import pytest
from conftest import (
    EXPECTED_PAGE_THEMES,
    REQUIRED_ROUTES,
    section_with_heading,
    without_version,
)
from flask import Flask

from app import create_app
from app.content.portfolio import PERSON
from app.content.projects import PROJECTS

EXPECTED_PROJECT_LINKS = {
    f"/projects/{project['slug']}": project for project in PROJECTS.values()
}
SOCIAL_PREVIEW_URL = (
    "http://localhost/static/images/brand/social-preview-placeholder.svg"
)
EXTERNAL_REFERENCE_PATTERN = re.compile(
    r"(?:https?://|mailto:|tel:)[^\s\"'<>]+"
)


def rendered_values(document):
    values = [document.text]
    for node in document.find_all():
        values.extend(
            str(value) for value in node.attrs.values() if value is not None
        )
    return values


def rendered_audit_surface(document):
    return " ".join(rendered_values(document)).casefold()


def rendered_external_references(document):
    return {
        match.group(0).rstrip(".,);")
        for value in rendered_values(document)
        for match in EXTERNAL_REFERENCE_PATTERN.finditer(value)
    }


def test_application_factory_returns_flask_app():
    application = create_app({"TESTING": True})
    assert isinstance(application, Flask)
    assert application.testing is True
    assert application.debug is False


@pytest.mark.parametrize(
    "path",
    ["/", "/research", "/about", "/contact", "/robots.txt", "/sitemap.xml"],
)
def test_main_routes_respond(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_home_contains_primary_navigation(client):
    html = client.get("/").get_data(as_text=True)
    for href in ["/", "/projects", "/experience", "/research", "/about", "/contact"]:
        assert f'href="{href}"' in html


@pytest.mark.parametrize("path", REQUIRED_ROUTES)
def test_every_required_route_responds_successfully(client, path):
    assert client.get(path).status_code == 200


def test_every_required_route_has_unique_title_and_description(client, parse_html):
    titles = set()
    descriptions = set()

    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        head = document.find_one("head")
        title = head.find_one("title").text
        description = head.find_one("meta", name="description").attrs["content"]

        assert title
        assert description
        assert title not in titles
        assert description not in descriptions
        titles.add(title)
        descriptions.add(description)


@pytest.mark.parametrize("path, expected_theme", EXPECTED_PAGE_THEMES.items())
def test_required_routes_render_the_approved_page_theme(
    client, parse_html, path, expected_theme
):
    document = parse_html(client.get(path).get_data(as_text=True))
    body = document.find_one("body")

    assert body.classes & {"theme-dark", "theme-editorial"} == {expected_theme}


def test_custom_404(client):
    response = client.get("/missing-page")
    assert response.status_code == 404
    assert "Page not found" in response.get_data(as_text=True)


def test_custom_500(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/_test-500")
    def trigger_test_error():
        raise RuntimeError("forced test error")

    response = client.get("/_test-500")
    assert response.status_code == 500
    assert "The system hit an unexpected error." in response.get_data(as_text=True)


def test_home_renders_every_required_section(client):
    html = client.get("/").get_data(as_text=True)
    for section_id in [
        "hero",
        "project-explorer",
        "featured-projects",
        "experience",
        "research",
        "skills",
        "leadership",
        "about",
        "contact",
    ]:
        assert f'id="{section_id}"' in html


def test_home_constellation_has_complete_native_and_fallback_links(
    client, parse_html
):
    document = parse_html(client.get("/").get_data(as_text=True))
    constellation = document.find_one("div", class_="constellation")
    native_links = constellation.find_all("a", class_="constellation__node")
    fallback = document.find_one("div", class_="constellation-fallback")
    fallback_links = fallback.find_all("a")

    expected_native_links = [
        (project["slug"], href, project["name"])
        for href, project in EXPECTED_PROJECT_LINKS.items()
    ]
    expected_fallback_links = [
        (href, project["name"], project["description"])
        for href, project in EXPECTED_PROJECT_LINKS.items()
    ]

    assert len(native_links) == len(expected_native_links)
    assert [
        (
            link.attrs["data-node"],
            link.attrs["href"],
            link.find_one("strong").text,
        )
        for link in native_links
    ] == expected_native_links
    assert len(fallback_links) == len(expected_fallback_links)
    assert [
        (
            link.attrs["href"],
            link.find_one("strong").text,
            link.find_one("span").text,
        )
        for link in fallback_links
    ] == expected_fallback_links


def test_home_constellation_uses_exact_concept_labels_and_disclaimer(
    client, parse_html
):
    document = parse_html(client.get("/").get_data(as_text=True))
    concepts = document.find_one("div", class_="constellation__concepts")
    concept_sections = concepts.find_all("section")
    concept_keys = [
        section.attrs.get("data-concept") for section in concept_sections
    ]

    assert len(concept_sections) == len(PROJECTS)
    assert concept_keys == list(PROJECTS)
    assert len(concept_keys) == len(set(concept_keys))
    sections = dict(zip(concept_keys, concept_sections))
    assert sections["tracksense"].find_one("h3").text == (
        "Possible relative-risk path"
    )
    assert sections["tracksense"].find_one("p").text == (
        "Nut butter jar → cutlery → bread → plate"
    )
    assert sections["tracksense"].find_one("small").text == (
        "This illustrates possible propagation, not confirmed contamination."
    )
    assert sections["forebid"].find_one("h3").text == (
        "Trust-aware market context"
    )
    assert sections["forebid"].find_one("p").text == (
        "Market snapshot · Trust weighting · Agent reputation · "
        "Outlier filtering · Fair price"
    )
    assert sections["engram-pipeline"].find_one("h3").text == (
        "Reviewable public-source research"
    )
    assert sections["engram-pipeline"].find_one("p").text == (
        "Public company sources · Seniority filtering · Source verification · "
        "Human review · Re-runnable pipeline"
    )


def test_project_index_renders_every_complete_project_entry(client, parse_html):
    document = parse_html(client.get("/projects").get_data(as_text=True))
    project_list = document.find_one("section", class_="project-list")
    previews = project_list.find_all("article", class_="project-preview")

    assert len(previews) == len(EXPECTED_PROJECT_LINKS)
    rendered = {}
    for preview in previews:
        link = preview.find_one("a")
        rendered[link.attrs["href"]] = {
            "name": link.text,
            "description": preview.find_one("p").text,
            "status": preview.find_one("span", class_="status-badge").text,
        }

    assert rendered == {
        href: {
            "name": project["name"],
            "description": project["description"],
            "status": project["status"],
        }
        for href, project in EXPECTED_PROJECT_LINKS.items()
    }


def test_experience_index_links_to_complete_engram_story(client, parse_html):
    document = parse_html(client.get("/experience").get_data(as_text=True))
    link = document.find_one("a", href="/experience/engram")

    assert link.text == "Read the full experience →"
    assert "Engram" in document.find_one("main").text


def test_tracksense_case_study_contains_required_content(client):
    html = client.get("/projects/tracksense").get_data(as_text=True)
    assert "Founder and Sole Developer" in html
    assert "92-test suite" in html
    assert "possible cross-contact" in html.lower()
    assert "does not chemically detect allergens" in html.lower()
    for heading in [
        "Overview",
        "Problem",
        "Core insight",
        "System architecture",
        "Detection system",
        "Object tracking",
        "Contact tracking",
        "Risk propagation",
        "Dataset engineering",
        "Co-detection failure",
        "Root-cause analysis",
        "Synthetic data solution",
        "Testing",
        "Results",
        "Limitations",
        "Research report",
    ]:
        assert f">{heading}<" in html


def test_tracksense_external_link(client):
    html = client.get("/projects/tracksense").get_data(as_text=True)
    assert "https://github.com/anantmehta20100-ant/tracksense" in html


def test_tracksense_test_count_comes_from_central_content(client, monkeypatch):
    monkeypatch.setitem(PROJECTS["tracksense"], "test_count", 137)

    html = client.get("/projects/tracksense").get_data(as_text=True)

    assert "137-test suite" in html
    assert "92-test suite" not in html


def test_forebid_case_study_separates_shipped_and_planned_work(client):
    html = client.get("/projects/forebid").get_data(as_text=True)
    assert "Illustrative interface data — not live financial data." in html
    assert "Current prototype" in html
    assert "Production roadmap" in html
    assert "Register ForeBid in the NANDA Index" in html
    assert "https://nanda-payments.replit.app/" in html
    assert html.index("Current prototype") < html.index("Production roadmap")


def test_engram_project_and_experience_routes(client):
    project = client.get("/projects/engram-pipeline")
    experience = client.get("/experience/engram")
    assert project.status_code == 200
    assert experience.status_code == 200
    for response in [project, experience]:
        html = response.get_data(as_text=True)
        assert "Finance Expert Discovery Pipeline" in html
        assert "Built using AI coding agents under my direction." in html
        assert "Replaced a manual, one-at-a-time research process" in html


def test_engram_project_mock_table_contains_only_approved_rows(
    client, parse_html
):
    document = parse_html(
        client.get("/projects/engram-pipeline").get_data(as_text=True)
    )
    mock_output = section_with_heading(document, "Mock output")
    table = mock_output.find_one("table")
    rows = [
        tuple(cell.text for cell in row.find_all("td"))
        for row in table.find_one("tbody").find_all("tr")
    ]

    assert rows == [
        (
            "Executive A",
            "Example Capital",
            "Executive biography",
            "Sample biography URL",
        ),
        (
            "Partner B",
            "Example Capital",
            "Leadership page",
            "Sample biography URL",
        ),
        (
            "Managing Director C",
            "Example Capital",
            "Team page",
            "Sample biography URL",
        ),
    ]
    assert not mock_output.find_all("a")


def test_engram_experience_mock_list_contains_only_approved_identities(
    client, parse_html
):
    document = parse_html(client.get("/experience/engram").get_data(as_text=True))
    mock_output = section_with_heading(document, "Mock output")

    assert [item.text for item in mock_output.find_one("ul").find_all("li")] == [
        "Executive A · Example Capital",
        "Partner B · Example Capital",
        "Managing Director C · Example Capital",
    ]
    assert "Sample biography URL" not in mock_output.text
    assert not mock_output.find_all("a")


@pytest.mark.parametrize(
    "path", ["/projects/engram-pipeline", "/experience/engram"]
)
def test_engram_pages_exclude_private_and_unsupported_details(
    client, parse_html, path
):
    document = parse_html(client.get(path).get_data(as_text=True))
    visible_text = document.find_one("body").text.casefold()

    for forbidden in [
        "linkedin",
        "record count",
        "unpaid internship",
        "real executive name",
        "private email address",
        "private phone number",
    ]:
        assert forbidden not in visible_text


def test_engram_confidential_work_uses_only_the_approved_sentence(
    client, parse_html
):
    document = parse_html(client.get("/experience/engram").get_data(as_text=True))
    confidential = section_with_heading(document, "Ongoing confidential work")

    assert confidential.find_one("p").text == (
        "Contributing to an additional internal project under confidentiality."
    )


def test_about_contains_confirmed_narrative(client):
    html = client.get("/about").get_data(as_text=True)
    assert "Bombay International School" in html
    assert "WRO, FTC, and FRC" in html
    assert "hands-on internship" in html
    assert "university major" not in html


def test_contact_contains_confirmed_actions(client):
    html = client.get("/contact").get_data(as_text=True)
    assert "anantmehta20100@gmail.com" in html
    assert 'href="mailto:anantmehta20100@gmail.com"' in html
    assert "https://github.com/anantmehta20100-ant" in html
    assert "Copy email" in html
    assert "LinkedIn" not in html


def test_research_uses_crest_report_language(client):
    html = client.get("/research").get_data(as_text=True)
    assert "CREST project report" in html
    assert "journal publication" not in html
    assert "/projects/tracksense" in html


def test_resume_cannot_be_opened_or_downloaded(client, parse_html):
    for unavailable_path in [
        "/resume",
        "/resume.pdf",
        "/resume/download",
        "/static/documents/resume.pdf",
    ]:
        assert client.get(unavailable_path).status_code == 404

    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        assert not [
            anchor
            for anchor in document.find_all("a")
            if anchor.attrs.get("href", "").startswith("/resume")
        ]


def test_public_pages_exclude_unsupported_claims(client, parse_html):
    forbidden_phrases = [
        "definitively detects contamination",
        "confirms contamination",
        "journal publication",
        "linkedin",
        "unpaid",
        "historically strong result",
    ]

    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        audit_surface = rendered_audit_surface(document)
        for phrase in forbidden_phrases:
            assert phrase.casefold() not in audit_surface, (
                f"{path} rendered unsupported claim {phrase!r}"
            )


@pytest.mark.parametrize(
    "markup, hidden_value",
    [
        (
            '<html><body><a href="https://linkedin.com/in/private"></a></body></html>',
            "linkedin",
        ),
        (
            '<html><body><img alt="Private email address"></body></html>',
            "private email address",
        ),
        (
            '<html><body><div aria-label="Unpaid internship"></div></body></html>',
            "unpaid internship",
        ),
        (
            (
                '<html><head><meta content="Historically strong result"></head>'
                "<body></body></html>"
            ),
            "historically strong result",
        ),
        (
            (
                '<html><head><script type="application/ld+json">'
                '{"sameAs":["https://linkedin.com/in/private"]}'
                "</script></head><body></body></html>"
            ),
            "linkedin",
        ),
    ],
)
def test_sensitive_audit_surface_includes_hidden_values(
    parse_html, markup, hidden_value
):
    assert hidden_value in rendered_audit_surface(parse_html(markup))


def test_public_pages_use_only_approved_external_references(client, parse_html):
    base_references = {
        "http://localhost/",
        "https://schema.org",
        PERSON["github"],
        f"mailto:{PERSON['email']}",
        SOCIAL_PREVIEW_URL,
    }
    route_references = {
        "/projects/tracksense": {PROJECTS["tracksense"]["github"]},
        "/projects/forebid": {PROJECTS["forebid"]["live_demo"]},
    }

    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        expected = base_references | {f"http://localhost{path}"}
        expected |= route_references.get(path, set())

        found = {
            without_version(reference)
            for reference in rendered_external_references(document)
        }

        assert found == expected
