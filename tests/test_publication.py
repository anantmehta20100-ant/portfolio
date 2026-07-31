import importlib

import app as app_module
from app import create_app
from app.content import publication
from app.content.publication import (
    RESUME_PATH,
    RESUME_PUBLISHED,
    TRACKSENSE_REPORT_PATH,
    TRACKSENSE_REPORT_PUBLISHED,
    report_is_available,
    resume_is_available,
)


def test_resume_is_not_published():
    assert RESUME_PUBLISHED is False


def test_resume_availability_requires_both_flag_and_file(tmp_path):
    document = tmp_path / RESUME_PATH
    document.parent.mkdir(parents=True)
    document.write_bytes(b"%PDF-1.4\n")

    assert resume_is_available(tmp_path) is False
    assert resume_is_available(tmp_path, published=False) is False
    assert resume_is_available(tmp_path, published=True) is True


def test_report_path_is_exact():
    assert TRACKSENSE_REPORT_PUBLISHED is True
    assert TRACKSENSE_REPORT_PATH == "documents/TrackSense_CREST_Report_Main.pdf"


def test_report_availability_tracks_real_file(tmp_path):
    assert report_is_available(tmp_path) is False
    report = tmp_path / TRACKSENSE_REPORT_PATH
    report.parent.mkdir(parents=True)
    report.write_bytes(b"%PDF-1.4\n")
    assert report_is_available(tmp_path) is True


def test_flask_config_defaults_follow_publication_contract(monkeypatch):
    with monkeypatch.context() as patched:
        patched.setattr(publication, "RESUME_PUBLISHED", True)
        patched.setattr(publication, "TRACKSENSE_REPORT_PUBLISHED", False)
        reloaded_app = importlib.reload(app_module)

        application = reloaded_app.create_app({"TESTING": True})

        assert application.config["RESUME_PUBLISHED"] is True
        assert application.config["TRACKSENSE_REPORT_PUBLISHED"] is False

    importlib.reload(app_module)


def test_resume_absent_keeps_control_disabled(tmp_path):
    app = create_app({"TESTING": True, "STATIC_FOLDER": str(tmp_path)})
    client = app.test_client()

    html = client.get("/").get_data(as_text=True)

    assert "Resume — Coming Soon" in html
    assert 'href="/resume' not in html
    assert client.get("/resume").status_code == 404


def test_resume_flag_alone_never_exposes_a_missing_file(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "STATIC_FOLDER": str(tmp_path),
            "RESUME_PUBLISHED": True,
        }
    )
    client = app.test_client()

    html = client.get("/").get_data(as_text=True)

    assert "Resume — Coming Soon" in html
    assert 'href="/resume' not in html
    assert client.get("/resume").status_code == 404


def test_resume_publishes_only_when_flag_and_file_agree(tmp_path):
    document = tmp_path / RESUME_PATH
    document.parent.mkdir(parents=True)
    document.write_bytes(b"%PDF-1.4\n")
    app = create_app(
        {
            "TESTING": True,
            "STATIC_FOLDER": str(tmp_path),
            "RESUME_PUBLISHED": True,
        }
    )
    client = app.test_client()

    html = client.get("/").get_data(as_text=True)

    assert 'href="/resume"' in html
    assert "Resume — Coming Soon" not in html
    assert client.get("/resume").status_code == 200
    download = client.get("/resume?download=1")
    assert "attachment" in download.headers["Content-Disposition"]


def test_resume_file_alone_never_publishes_without_the_flag(tmp_path):
    document = tmp_path / RESUME_PATH
    document.parent.mkdir(parents=True)
    document.write_bytes(b"%PDF-1.4\n")
    app = create_app({"TESTING": True, "STATIC_FOLDER": str(tmp_path)})
    client = app.test_client()

    assert "Resume — Coming Soon" in client.get("/").get_data(as_text=True)
    assert client.get("/resume").status_code == 404


def test_report_absent_disables_links(tmp_path):
    app = create_app({"TESTING": True, "STATIC_FOLDER": str(tmp_path)})
    html = app.test_client().get("/projects/tracksense").get_data(as_text=True)
    research_html = app.test_client().get("/research").get_data(as_text=True)
    assert "Report file awaiting placement" in html
    assert 'href="/projects/tracksense/report' not in html
    assert "Report file awaiting placement" in research_html
    assert 'href="/projects/tracksense/report' not in research_html
    assert app.test_client().get("/projects/tracksense/report").status_code == 404


def test_report_present_supports_view_and_download(tmp_path):
    report = tmp_path / TRACKSENSE_REPORT_PATH
    report.parent.mkdir(parents=True)
    report.write_bytes(b"%PDF-1.4\n")
    app = create_app({"TESTING": True, "STATIC_FOLDER": str(tmp_path)})
    client = app.test_client()
    html = client.get("/projects/tracksense").get_data(as_text=True)
    research_html = client.get("/research").get_data(as_text=True)
    assert 'href="/projects/tracksense/report"' in html
    assert 'href="/projects/tracksense/report?download=1"' in html
    assert 'href="/projects/tracksense/report"' in research_html
    assert 'href="/projects/tracksense/report?download=1"' in research_html
    assert client.get("/projects/tracksense/report").status_code == 200
    download = client.get("/projects/tracksense/report?download=1")
    assert "attachment" in download.headers["Content-Disposition"]


def test_app_config_can_unpublish_existing_report(tmp_path):
    report = tmp_path / TRACKSENSE_REPORT_PATH
    report.parent.mkdir(parents=True)
    report.write_bytes(b"%PDF-1.4\n")
    app = create_app(
        {
            "TESTING": True,
            "STATIC_FOLDER": str(tmp_path),
            "TRACKSENSE_REPORT_PUBLISHED": False,
        }
    )
    client = app.test_client()

    for path in ["/projects/tracksense", "/research"]:
        html = client.get(path).get_data(as_text=True)
        assert "Report file awaiting placement" in html
        assert 'href="/projects/tracksense/report' not in html

    assert client.get("/projects/tracksense/report").status_code == 404


def test_report_publication_disabled_blocks_real_file(tmp_path, monkeypatch):
    report = tmp_path / TRACKSENSE_REPORT_PATH
    report.parent.mkdir(parents=True)
    report.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(publication, "TRACKSENSE_REPORT_PUBLISHED", False)
    app = create_app({"TESTING": True, "STATIC_FOLDER": str(tmp_path)})
    client = app.test_client()

    html = client.get("/projects/tracksense").get_data(as_text=True)

    assert "Report file awaiting placement" in html
    assert 'href="/projects/tracksense/report' not in html
    assert client.get("/projects/tracksense/report").status_code == 404
