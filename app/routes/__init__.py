from flask import current_app

from app.content.publication import report_is_available, resume_is_available


def tracksense_report_available() -> bool:
    return report_is_available(
        current_app.static_folder,
        published=current_app.config["TRACKSENSE_REPORT_PUBLISHED"],
    )


def resume_available() -> bool:
    return resume_is_available(
        current_app.static_folder,
        published=current_app.config["RESUME_PUBLISHED"],
    )
