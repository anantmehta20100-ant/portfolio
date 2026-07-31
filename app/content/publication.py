from __future__ import annotations

from pathlib import Path

RESUME_PUBLISHED = False
RESUME_PATH = "documents/Anant_Nitai_Mehta_Resume.pdf"
TRACKSENSE_REPORT_PUBLISHED = True
TRACKSENSE_REPORT_PATH = "documents/TrackSense_CREST_Report_Main.pdf"


def _is_available(
    static_folder: str | Path,
    relative_path: str | None,
    published: bool,
) -> bool:
    # Both gates must hold: the flag alone never exposes a document, and an
    # unset path or missing file keeps it closed even if the flag is flipped.
    if not published or not relative_path:
        return False
    return (Path(static_folder) / relative_path).is_file()


def report_is_available(
    static_folder: str | Path,
    *,
    published: bool | None = None,
) -> bool:
    if published is None:
        published = TRACKSENSE_REPORT_PUBLISHED
    return _is_available(static_folder, TRACKSENSE_REPORT_PATH, published)


def resume_is_available(
    static_folder: str | Path,
    *,
    published: bool | None = None,
) -> bool:
    if published is None:
        published = RESUME_PUBLISHED
    return _is_available(static_folder, RESUME_PATH, published)
