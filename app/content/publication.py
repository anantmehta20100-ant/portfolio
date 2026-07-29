from __future__ import annotations

from pathlib import Path

RESUME_PUBLISHED = False
RESUME_PATH = None
TRACKSENSE_REPORT_PUBLISHED = True
TRACKSENSE_REPORT_PATH = "documents/TrackSense_CREST_Report_Main.pdf"


def report_is_available(
    static_folder: str | Path,
    *,
    published: bool | None = None,
) -> bool:
    if published is None:
        published = TRACKSENSE_REPORT_PUBLISHED
    if not published:
        return False
    return (Path(static_folder) / TRACKSENSE_REPORT_PATH).is_file()
