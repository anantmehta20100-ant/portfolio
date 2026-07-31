from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, render_template

# Static assets are immutable per deploy because every URL carries a digest of
# that file, so they can be cached hard. Documents served through the gated
# routes keep their own short max-age since their URLs never change.
STATIC_MAX_AGE = timedelta(days=365)

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
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or any(character.isspace() for character in origin)
    ):
        raise ValueError(
            "CANONICAL_BASE_URL must be an HTTP(S) origin without a path, "
            "query, fragment, or credentials"
        )

    return f"{parsed.scheme}://{parsed.netloc.lower()}"


def _static_versions(static_folder: str | None) -> dict[str, str]:
    # Digest each file separately so an asset's URL changes only when that
    # asset changes; a shared digest would churn every cached URL on any edit.
    root = Path(static_folder) if static_folder else None
    if root is None or not root.is_dir():
        return {}

    versions = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        stat = path.stat()
        digest = hashlib.sha256(f"{stat.st_size}:{stat.st_mtime_ns}".encode())
        versions[path.relative_to(root).as_posix()] = digest.hexdigest()[:10]
    return versions


def create_app(test_config: dict | None = None) -> Flask:
    config = dict(test_config or {})
    static_folder = config.pop("STATIC_FOLDER", "static")
    app = Flask(__name__, static_folder=static_folder)
    app.config.from_mapping(
        CANONICAL_BASE_URL=os.environ.get("CANONICAL_BASE_URL", ""),
        RESUME_PUBLISHED=publication.RESUME_PUBLISHED,
        TRACKSENSE_REPORT_PUBLISHED=publication.TRACKSENSE_REPORT_PUBLISHED,
        SEND_FILE_MAX_AGE_DEFAULT=STATIC_MAX_AGE,
    )
    app.config.update(config)
    app.config["CANONICAL_BASE_URL"] = _normalize_canonical_base_url(
        app.config["CANONICAL_BASE_URL"]
    )

    static_versions = _static_versions(app.static_folder)

    @app.url_defaults
    def add_static_version(endpoint, values):
        if endpoint != "static":
            return
        version = static_versions.get(values.get("filename", ""))
        if version:
            values["v"] = version

    @app.context_processor
    def inject_portfolio_context():
        return {
            "navigation": NAVIGATION,
            "person": PERSON,
            "resume_published": app.config["RESUME_PUBLISHED"],
            # templates gate on this, not the bare flag: the resume stays
            # hidden until an approved file actually exists on disk
            "resume_available": publication.resume_is_available(
                app.static_folder,
                published=app.config["RESUME_PUBLISHED"],
            ),
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
