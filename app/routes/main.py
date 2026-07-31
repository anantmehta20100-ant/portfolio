from flask import Blueprint, Response, current_app, render_template, request

from app.content.portfolio import (
    ACHIEVEMENTS,
    EXPERIENCE,
    PERSON,
    RESEARCH,
    SKILL_GROUPS,
)
from app.content.projects import PROJECTS
from app.routes import tracksense_report_available

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    return render_template(
        "home.html",
        projects=PROJECTS,
        experience=EXPERIENCE,
        research=RESEARCH,
        skill_groups=SKILL_GROUPS,
        achievements=ACHIEVEMENTS,
        page_title="Anant Nitai Mehta | AI, Robotics and Computer Vision",
        page_description=(
            "Portfolio of Anant Nitai Mehta, a student developer from Mumbai "
            "building projects in artificial intelligence, computer vision, "
            "robotics and technical research."
        ),
        page_theme="dark",
    )


@bp.get("/research")
def research():
    return render_template(
        "research.html",
        research=RESEARCH,
        report_available=tracksense_report_available(),
        page_title="Research | Anant Nitai Mehta",
        page_description="Technical research and writing by Anant Nitai Mehta.",
        page_theme="editorial",
    )


@bp.get("/about")
def about():
    return render_template(
        "about.html",
        person=PERSON,
        page_title="About | Anant Nitai Mehta",
        page_description="About Anant Nitai Mehta, a student developer in Mumbai.",
        page_theme="editorial",
    )


@bp.get("/contact")
def contact():
    return render_template(
        "contact.html",
        person=PERSON,
        page_title="Contact | Anant Nitai Mehta",
        page_description="Contact Anant Nitai Mehta about internships and collaboration.",
        page_theme="editorial",
    )


@bp.get("/robots.txt")
def robots():
    base = (current_app.config.get("CANONICAL_BASE_URL") or request.url_root).rstrip(
        "/"
    )
    return Response(
        f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n",
        mimetype="text/plain",
    )


@bp.get("/sitemap.xml")
def sitemap():
    paths = [
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
    ]
    base = (current_app.config.get("CANONICAL_BASE_URL") or request.url_root).rstrip(
        "/"
    )
    body = "".join(f"<url><loc>{base}{path}</loc></url>" for path in paths)
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{body}</urlset>",
        mimetype="application/xml",
    )
