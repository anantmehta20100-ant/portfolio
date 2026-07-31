# Anant Nitai Mehta — Personal Technology Portfolio

A Flask portfolio presenting Anant’s practical work in AI, robotics, computer vision, applied research, and engineering systems.

## Stack

- Python 3
- Flask and Jinja
- HTML5 and modern CSS
- Vanilla JavaScript
- SVG
- pytest
- Gunicorn

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000`.

## Production-style run

```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

## Tests and checks

```bash
python -m pytest -v
python -m ruff check app tests run.py wsgi.py
python -m compileall -q app run.py wsgi.py
```

## Editing portfolio content

Edit identity, navigation, skills, research, achievements, and experience in `app/content/portfolio.py`. Edit TrackSense, ForeBid, and Finance Expert Discovery Pipeline content in `app/content/projects.py`.

## Replacing media

Add approved files to:

- `app/static/images/profile/`
- `app/static/images/tracksense/`
- `app/static/images/forebid/`
- `app/static/images/engram/`

Replace the matching media-placeholder macro call only after the real asset exists. Do not replace placeholders with generated product screenshots.

## TrackSense report

Place the approved CREST project report at:

`app/static/documents/TrackSense_CREST_Report_Main.pdf`

The View Report and Download PDF actions activate only when the real file exists and `TRACKSENSE_REPORT_PUBLISHED` remains enabled.

## Resume activation

The resume is currently unpublished. To activate it:

1. Obtain approval for the exact PDF.
2. Save it as `app/static/documents/Anant_Nitai_Mehta_Resume.pdf`, or change `RESUME_PATH` in `app/content/publication.py` to match the filename you use.
3. Set `RESUME_PUBLISHED = True` in `app/content/publication.py`.

The `/resume` route and the homepage control are already wired and tested, so no template or routing change is needed. Both gates must agree: the flag alone will not expose a missing file, and a file alone will not publish without the flag. The route is deliberately kept out of `sitemap.xml`.

## Deployment

Deploy `wsgi:app` to a Python-compatible host. Export `CANONICAL_BASE_URL` before
starting Gunicorn so the application factory loads the public production origin:

```bash
CANONICAL_BASE_URL=https://portfolio.example gunicorn --bind 0.0.0.0:8000 wsgi:app
```

The value must be an HTTP(S) origin without a path, query, fragment, or
credentials. A trailing slash is normalized automatically, and an invalid value
stops application startup. Keep debug mode disabled. Serve static files through
the platform or a reverse proxy in production.

Static assets are cached for a year. Every `/static/` URL carries a `?v=` digest
of that file's size and modification time, computed once at startup, so a deploy
invalidates only the assets that actually changed. Restart the application after
replacing a static file — the digests are not recomputed per request. The gated
report and resume routes set `max-age=0` instead, because their URLs never
change and they must revalidate.

## Privacy and credibility

- Do not add real Engram dataset rows, identities, counts, private data, or confidential work details.
- Do not describe TrackSense as chemically detecting allergens or confirming contamination or safety.
- Do not present ForeBid roadmap items as shipped.
- Do not publish a resume, LinkedIn profile, or real project media without explicit approval.

## Real-world inputs still required

- Profile photograph
- Approved resume
- TrackSense screenshots and demo media
- ForeBid screenshot and demo media
- Anonymized Engram pipeline preview
- LinkedIn URL, if publication is later approved
