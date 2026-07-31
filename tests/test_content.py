from flask import render_template_string

from app.content.portfolio import ACHIEVEMENTS, NAVIGATION, PERSON, SKILL_GROUPS
from app.content.projects import PROJECTS


def test_person_contains_confirmed_identity():
    assert PERSON["name"] == "Anant Nitai Mehta"
    assert PERSON["location"] == "Mumbai, India"
    assert PERSON["school"] == "Bombay International School"
    assert PERSON["email"] == "anantmehta20100@gmail.com"
    assert PERSON["github"] == "https://github.com/anantmehta20100-ant"


def test_navigation_contains_required_tabs():
    assert [item["label"] for item in NAVIGATION] == [
        "Home",
        "Projects",
        "Experience",
        "Research",
        "About",
        "Contact",
    ]


def test_project_records_have_required_fields():
    required = {"slug", "name", "role", "status", "description", "technologies"}
    assert set(PROJECTS) == {"tracksense", "forebid", "engram-pipeline"}
    for project in PROJECTS.values():
        assert required <= project.keys()


def test_engram_pages_render_one_shared_pipeline(client, parse_html):
    steps = PROJECTS["engram-pipeline"]["architecture"]
    rendered = []

    for path in ["/projects/engram-pipeline", "/experience/engram"]:
        document = parse_html(client.get(path).get_data(as_text=True))
        flow = document.find_one("ol", class_="architecture-flow")
        rendered.append([item.text for item in flow.find_all("li")])
        assert flow.attrs["aria-label"]

    assert rendered[0] == steps
    assert rendered[1] == steps


def test_every_architecture_flow_is_labelled(client, parse_html):
    for path in [
        "/projects/tracksense",
        "/projects/forebid",
        "/projects/engram-pipeline",
        "/experience/engram",
    ]:
        document = parse_html(client.get(path).get_data(as_text=True))
        for flow in document.find_all("ol", class_="architecture-flow"):
            assert flow.attrs.get("aria-label"), f"{path} has an unlabelled flow"


def test_skill_groups_and_achievements_are_nonempty():
    assert {group["name"] for group in SKILL_GROUPS} == {"Core", "Familiar"}
    assert all(group["items"] for group in SKILL_GROUPS)
    assert ACHIEVEMENTS


def test_template_context_includes_shared_portfolio_content(app):
    with app.test_request_context():
        assert (
            render_template_string(
                "{{ person.name }}|{{ navigation|length }}|"
                "{{ resume_published }}|{{ resume_available }}"
            )
            == "Anant Nitai Mehta|6|False|False"
        )
