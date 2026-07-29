from flask import Blueprint, render_template

from app.content.portfolio import EXPERIENCE
from app.content.projects import PROJECTS

bp = Blueprint("experience", __name__, url_prefix="/experience")


@bp.get("")
def index():
    return render_template(
        "experience/index.html",
        experience=EXPERIENCE,
        page_title="Experience | Anant Nitai Mehta",
        page_description=(
            "Engineering experience and applied research work by Anant Nitai Mehta."
        ),
        page_theme="dark",
    )


@bp.get("/engram")
def engram():
    return render_template(
        "experience/engram.html",
        experience=EXPERIENCE,
        project=PROJECTS["engram-pipeline"],
        page_title="Engram Experience | Anant Nitai Mehta",
        page_description=(
            "Anant Nitai Mehta’s internship experience and public-source research "
            "pipeline work at Engram."
        ),
        page_theme="editorial",
    )
