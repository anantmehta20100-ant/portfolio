from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

from flask import Flask, render_template

from app.content import publication
from app.content.portfolio import NAVIGATION, PERSON


def _normalize_canonical_base_url(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError("CANONICAL_BASE_URL must be a string HTTP(S) origin")

    origin = value.strip()
    if not origin:
        return ""

    parsed = urlsplit(origin)
    try:
        # urlsplit defers port validation; reading the property is what raises
        _ = parsed.port
    except ValueError as error:
        raise ValueError(
            "CANONICAL_BASE_URL must be a valid HTTP(S) origin"
        ) from error

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or any(character.isspace() for character in origin)
    ):
        raise ValueError(
            "CANONICAL_BASE_URL must be an HTTP(S) origin without a path, "
            "query, fragment, or credentials"
        )

    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def create_app(test_config: dict | None = None) -> Flask:
    config = dict(test_config or {})
    static_folder = config.pop("STATIC_FOLDER", "static")
    app = Flask(__name__, static_folder=static_folder)
    app.config.from_mapping(
        CANONICAL_BASE_URL=os.environ.get("CANONICAL_BASE_URL", ""),
        RESUME_PUBLISHED=publication.RESUME_PUBLISHED,
        TRACKSENSE_REPORT_PUBLISHED=publication.TRACKSENSE_REPORT_PUBLISHED,
    )
    app.config.update(config)
    app.config["CANONICAL_BASE_URL"] = _normalize_canonical_base_url(
        app.config["CANONICAL_BASE_URL"]
    )

    @app.context_processor
    def inject_portfolio_context():
        return {
            "navigation": NAVIGATION,
            "person": PERSON,
            "resume_published": app.config["RESUME_PUBLISHED"],
        }

    app.jinja_env.globals["now"] = lambda: datetime.now(timezone.utc)

    @app.errorhandler(404)
    def not_found(error):
        return (
            render_template(
                "404.html",
                page_title="Page not found | Anant Nitai Mehta",
                page_description="The requested portfolio page could not be found.",
                page_theme="dark",
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(error):
        return (
            render_template(
                "500.html",
                page_title="Something went wrong | Anant Nitai Mehta",
                page_description="The portfolio encountered an unexpected error.",
                page_theme="dark",
            ),
            500,
        )

    from app.routes import experience, main, projects

    app.register_blueprint(main.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(experience.bp)
    return app
