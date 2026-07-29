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


def test_skill_groups_and_achievements_are_nonempty():
    assert {group["name"] for group in SKILL_GROUPS} == {"Core", "Familiar"}
    assert all(group["items"] for group in SKILL_GROUPS)
    assert ACHIEVEMENTS


def test_template_context_includes_shared_portfolio_content(app):
    with app.test_request_context():
        assert (
            render_template_string(
                "{{ person.name }}|{{ navigation|length }}|{{ resume_published }}"
            )
            == "Anant Nitai Mehta|6|False"
        )
