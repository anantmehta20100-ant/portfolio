import re
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).parents[1]
STATIC = ROOT / "app" / "static"
REQUIRED_ROUTES = (
    "/",
    "/projects",
    "/projects/tracksense",
    "/projects/forebid",
    "/projects/engram-pipeline",
    "/experience",
    "/experience/engram",
    "/research",
    "/about",
    "/contact",
)
PRIMARY_NAVIGATION = {
    "/": "Home",
    "/projects": "Projects",
    "/experience": "Experience",
    "/research": "Research",
    "/about": "About",
    "/contact": "Contact",
}


def css_declarations(css, selector):
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", css)
    assert match, f"Missing CSS rule for {selector}"
    return match.group(1)


def contrast_ratio(foreground, background):
    def luminance(value):
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def section_with_heading(document, heading):
    matches = [
        section
        for section in document.find_all("section")
        if any(node.text == heading for node in section.find_all("h2"))
    ]
    assert len(matches) == 1, (
        f"Expected one section headed {heading!r}, found {len(matches)}"
    )
    return matches[0]


def test_engram_mock_table_has_exact_caption_and_column_headers(
    client, parse_html
):
    document = parse_html(
        client.get("/projects/engram-pipeline").get_data(as_text=True)
    )
    mock_output = section_with_heading(document, "Mock output")
    table = mock_output.find_one("table")

    assert table.find_one("caption").text == (
        "Anonymized mock data — no real executive or company records are shown."
    )
    assert [
        header.text for header in table.find_one("thead").find_all("th")
    ] == ["Person", "Organisation", "Seniority signal", "Source"]
    assert {
        header.attrs.get("scope")
        for header in table.find_one("thead").find_all("th")
    } == {"col"}


def test_required_stylesheets_exist_and_are_loaded(client, parse_html):
    document = parse_html(client.get("/").get_data(as_text=True))
    styles = [
        "tokens.css",
        "base.css",
        "layout.css",
        "components.css",
        "dark.css",
        "editorial.css",
        "responsive.css",
    ]
    stylesheet_links = {
        link.attrs["href"]
        for link in document.find_all("link", rel="stylesheet")
    }
    for stylesheet in styles:
        assert (STATIC / "css" / stylesheet).is_file()
        assert f"/static/css/{stylesheet}" in stylesheet_links


def test_approved_visual_tokens_are_present():
    tokens = (STATIC / "css" / "tokens.css").read_text()
    for value in ["#08090d", "#f5f2ff", "#a78bfa", "#73d7e6", "#f2efe8"]:
        assert value in tokens
    assert "Avenir Next" in tokens


def test_required_media_directories_exist():
    for relative in [
        "images/profile",
        "images/tracksense",
        "images/forebid",
        "images/engram",
        "documents",
    ]:
        assert (STATIC / relative).is_dir()


def test_accessibility_foundations_render(client, parse_html):
    document = parse_html(client.get("/").get_data(as_text=True))
    skip_link = document.find_one("a", class_="skip-link")
    menu_toggle = document.find_one("button", class_="menu-toggle")
    main = document.find_one("main", id="main-content")

    assert skip_link.attrs["href"] == "#main-content"
    assert skip_link.text == "Skip to content"
    assert menu_toggle.attrs["aria-controls"] == "primary-navigation"
    assert menu_toggle.attrs["aria-expanded"] == "false"
    assert main.attrs["tabindex"] == "-1"


def test_mobile_navigation_is_visible_until_progressively_enhanced(client):
    html = client.get("/").get_data(as_text=True)
    components = (STATIC / "css" / "components.css").read_text()
    responsive = (STATIC / "css" / "responsive.css").read_text()

    assert "data-navigation-enhanced" not in html
    assert "display: none;" in css_declarations(components, ".menu-toggle")

    default_navigation = css_declarations(
        responsive, "[data-site-header] [data-primary-navigation]"
    )
    assert "display: grid;" in default_navigation
    assert "display: none;" not in default_navigation

    enhanced_toggle = css_declarations(
        responsive,
        '[data-site-header][data-navigation-enhanced="true"] .menu-toggle',
    )
    enhanced_navigation = css_declarations(
        responsive,
        '[data-site-header][data-navigation-enhanced="true"] '
        "[data-primary-navigation]",
    )
    enhanced_open_navigation = css_declarations(
        responsive,
        '[data-site-header][data-navigation-enhanced="true"] '
        '[data-primary-navigation][data-open="true"]',
    )
    assert "display: inline-flex;" in enhanced_toggle
    assert "display: none;" in enhanced_navigation
    assert "display: grid;" in enhanced_open_navigation


def test_constellation_uses_one_viewbox_coordinate_stage(client):
    html = client.get("/").get_data(as_text=True)
    dark = (STATIC / "css" / "dark.css").read_text()

    assert 'class="constellation__stage"' in html
    stage = css_declarations(dark, ".constellation__stage")
    assert "position: relative;" in stage
    assert "aspect-ratio: 920 / 520;" in stage

    anchors = {
        ".constellation__node--tracksense": (
            "24.4565217391%",
            "27.8846153846%",
        ),
        ".constellation__node--forebid": ("76.0869565217%", "27.8846153846%"),
        ".constellation__node--engram-pipeline": ("75%", "72.6923076923%"),
    }
    for selector, (left, top) in anchors.items():
        declarations = css_declarations(dark, selector)
        assert f"left: {left};" in declarations
        assert f"top: {top};" in declarations


def test_constellation_node_motion_hook_defaults_to_zero():
    dark = (STATIC / "css" / "dark.css").read_text()
    node = css_declarations(dark, ".constellation__node")

    assert (
        "transform: translate3d(var(--node-x, 0), var(--node-y, 0), 0);" in node
    )


def test_editorial_signal_meets_non_text_contrast_floor():
    tokens = (STATIC / "css" / "tokens.css").read_text()
    editorial = (STATIC / "css" / "editorial.css").read_text()
    match = re.search(r"--signal-on-paper:\s*(#[0-9a-fA-F]{6})", tokens)

    assert match
    assert contrast_ratio(match.group(1), "#f2efe8") >= 3
    for selector in [
        ".theme-editorial :focus-visible",
        ".theme-editorial .chart-line",
        ".theme-editorial .chart-points circle",
    ]:
        assert "var(--signal-on-paper)" in css_declarations(editorial, selector)


def test_primary_navigation_has_complete_links_and_active_page_semantics(
    client, parse_html
):
    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        navigation = document.find_one("nav", id="primary-navigation")
        links = navigation.find_all("a")
        page_links = {
            link.attrs["href"]: link.text
            for link in links
            if link.attrs.get("href", "").startswith("/")
        }

        assert navigation.attrs["aria-label"] == "Primary navigation"
        assert page_links == PRIMARY_NAVIGATION

        current_links = [
            link for link in links if link.attrs.get("aria-current") == "page"
        ]
        current_path = path
        if path.startswith("/projects/"):
            current_path = "/projects"
        elif path.startswith("/experience/"):
            current_path = "/experience"
        assert [(link.attrs["href"], link.text) for link in current_links] == [
            (current_path, PRIMARY_NAVIGATION[current_path])
        ]

        section_links = [
            link for link in links if "nav-section-link" in link.classes
        ]
        expected_section_links = (
            [("#featured-projects", "Selected work")] if path == "/" else []
        )
        assert [
            (link.attrs["href"], link.text) for link in section_links
        ] == expected_section_links


def test_external_links_are_labelled_and_safe(client, parse_html):
    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        external_links = [
            link
            for link in document.find_all("a")
            if link.attrs.get("href", "").startswith(("http://", "https://"))
        ]

        for link in external_links:
            assert link.attrs.get("target") == "_blank", (
                f"{path} external link {link.attrs['href']} must open in a new tab"
            )
            assert "noreferrer" in link.attrs.get("rel", "").split()
            assert "(opens in a new tab)" in link.text


def test_resume_control_is_accessibly_disabled(client, parse_html):
    document = parse_html(client.get("/").get_data(as_text=True))
    controls = document.find_all(**{"aria-disabled": "true"})

    assert len(controls) == 1
    control = controls[0]
    assert control.tag == "span"
    assert control.text == "Resume — Coming Soon"
    assert "button-disabled" in control.classes
    assert "href" not in control.attrs


def test_required_pages_have_logical_heading_order(client, parse_html):
    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))
        headings = document.find_one("main").find_all(
            tag=lambda actual: actual in {"h1", "h2", "h3", "h4", "h5", "h6"}
        )
        levels = [int(heading.tag[1]) for heading in headings]

        assert levels.count(1) == 1, f"{path} must have exactly one h1"
        assert levels[0] == 1, f"{path} must start its main heading outline with h1"
        assert all(
            current <= previous + 1 for previous, current in pairwise(levels)
        ), f"{path} skips a heading level: {levels}"


def test_media_and_tables_have_nonempty_accessible_labels(client, parse_html):
    for path in REQUIRED_ROUTES:
        document = parse_html(client.get(path).get_data(as_text=True))

        for image in document.find_all("img"):
            assert image.attrs.get("alt", "").strip(), (
                f"{path} has an image without useful alternative text"
            )

        for figure in document.find_all("figure"):
            captions = figure.find_all("figcaption")
            assert len(captions) == 1
            assert captions[0].text

        for image_role in document.find_all(role="img"):
            label = image_role.attrs.get("aria-label", "").strip()
            labelled_by = image_role.attrs.get("aria-labelledby", "").split()
            if labelled_by:
                referenced_text = [
                    document.find_one(id=reference).text
                    for reference in labelled_by
                ]
                assert all(referenced_text)
            else:
                assert label, f"{path} has role=img without an accessible name"

        for table in document.find_all("table"):
            assert table.find_one("caption").text
            headers = table.find_one("thead").find_all("th")
            assert headers
            assert all(header.text for header in headers)
            assert all(header.attrs.get("scope") == "col" for header in headers)
