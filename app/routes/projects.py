from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
)

from app.content.projects import PROJECTS
from app.content.publication import TRACKSENSE_REPORT_PATH
from app.routes import tracksense_report_available

bp = Blueprint("projects", __name__, url_prefix="/projects")


@bp.get("")
def index():
    return render_template(
        "projects/index.html",
        projects=PROJECTS,
        page_title="Projects | Anant Nitai Mehta",
        page_description=(
            "AI, computer vision, agent, and research pipeline projects "
            "by Anant Nitai Mehta."
        ),
        page_theme="dark",
    )


@bp.get("/tracksense")
def tracksense():
    return render_template(
        "projects/tracksense.html",
        project=PROJECTS["tracksense"],
        report_available=tracksense_report_available(),
        page_title="TrackSense Case Study | Anant Nitai Mehta",
        page_description=(
            "A technical case study of TrackSense, a prototype computer-vision "
            "system for possible allergen cross-contact risk propagation."
        ),
        page_theme="editorial",
    )


@bp.get("/forebid")
def forebid():
    return render_template(
        "projects/forebid.html",
        project=PROJECTS["forebid"],
        page_title="ForeBid Case Study | Anant Nitai Mehta",
        page_description=(
            "A case study of ForeBid, a trust-aware market-intelligence prototype "
            "for autonomous agents."
        ),
        page_theme="editorial",
    )


@bp.get("/engram-pipeline")
def engram_pipeline():
    return render_template(
        "projects/engram_pipeline.html",
        project=PROJECTS["engram-pipeline"],
        page_title="Finance Expert Discovery Pipeline | Anant Nitai Mehta",
        page_description=(
            "A technical view of a public-source, reviewable finance expert "
            "discovery pipeline."
        ),
        page_theme="editorial",
    )


@bp.get("/tracksense/report")
def tracksense_report():
    if not tracksense_report_available():
        abort(404)
    report = Path(TRACKSENSE_REPORT_PATH)
    return send_from_directory(
        Path(current_app.static_folder) / report.parent,
        report.name,
        as_attachment=request.args.get("download") == "1",
        download_name="TrackSense_CREST_Report_Main.pdf",
        # this URL never changes, so it must revalidate rather than inherit
        # the long max-age that digest-versioned static assets rely on
        max_age=0,
    )
