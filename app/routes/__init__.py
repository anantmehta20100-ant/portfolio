from flask import current_app

from app.content.publication import report_is_available


def tracksense_report_available() -> bool:
    return report_is_available(
        current_app.static_folder,
        published=current_app.config["TRACKSENSE_REPORT_PUBLISHED"],
    )
