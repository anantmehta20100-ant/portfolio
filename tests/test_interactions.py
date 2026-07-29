import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
STATIC = ROOT / "app" / "static"
JS = STATIC / "js"


def test_navigation_enhances_only_after_accessible_controller_is_ready():
    source = (JS / "navigation.js").read_text()

    assert 'setAttribute("aria-expanded", String(open))' in source
    assert "navigation.dataset.open = String(open)" in source
    assert 'event.key !== "Escape"' in source
    assert "toggle.focus()" in source
    assert 'header.dataset.navigationEnhanced = "true"' in source
    assert source.index('addEventListener("click"') < source.index(
        'header.dataset.navigationEnhanced = "true"'
    )
    assert source.index('addEventListener("keydown"') < source.index(
        'header.dataset.navigationEnhanced = "true"'
    )


def test_constellation_uses_cached_stage_anchors_and_capability_fallbacks():
    source = (JS / "constellation.js").read_text()

    for contract in [
        "requestAnimationFrame",
        "prefers-reduced-motion",
        "(pointer: coarse)",
        "saveData",
        "translate3d",
        'setProperty("--node-x"',
        'setProperty("--node-y"',
        "STAGE_WIDTH = 920",
        "STAGE_HEIGHT = 520",
        "ResizeObserver",
    ]:
        assert contract in source

    assert source.count("getBoundingClientRect()") == 1


def test_constellation_keyboard_state_survives_motion_fallbacks():
    source = (JS / "constellation.js").read_text()

    focus_handler = source.index('addEventListener("focus"')
    motion_exit = source.index("if (!motionAllowed) return")
    assert focus_handler < motion_exit
    assert 'addEventListener("blur"' in source
    assert 'path.dataset.active = String(active)' in source
    assert 'concept.dataset.active = String(active)' in source


def test_section_tracker_maps_home_sections_to_primary_routes():
    source = (JS / "section-tracker.js").read_text()

    assert "IntersectionObserver" in source
    for section_id, route in [
        ("hero", "/"),
        ("project-explorer", "/projects"),
        ("featured-projects", "/projects"),
        ("experience", "/experience"),
        ("research", "/research"),
        ("skills", "/about"),
        ("leadership", "/about"),
        ("about", "/about"),
        ("contact", "/contact"),
    ]:
        assert f'"{section_id}": "{route}"' in source
    assert 'setAttribute("aria-current", "location")' in source
    assert 'removeAttribute("aria-current")' in source


def test_tall_section_replaces_stale_current_navigation_state():
    source = (JS / "section-tracker.js").read_text()
    threshold_match = re.search(r"threshold:\s*\[([^\]]+)\]", source)

    assert threshold_match
    thresholds = [
        float(value.strip()) for value in threshold_match.group(1).split(",")
    ]

    viewport_height = 1000
    observer_root_height = viewport_height * (1 - 0.25 - 0.60)
    tall_section_height = viewport_height * 2
    maximum_intersection_ratio = observer_root_height / tall_section_height

    assert maximum_intersection_ratio < 0.15
    assert min(thresholds) <= maximum_intersection_ratio
    assert source.index('link.removeAttribute("aria-current")') < source.index(
        'link.setAttribute("aria-current", "location")'
    )


def test_location_tracking_uses_the_existing_active_navigation_style():
    components = (STATIC / "css" / "components.css").read_text()
    dark = (STATIC / "css" / "dark.css").read_text()

    assert 'a[aria-current="location"]::after' in components
    assert 'a[aria-current="location"]' in dark


def test_constellation_pointerleave_serializes_boolean_inactive_state():
    source = (JS / "constellation.js").read_text()

    assert "const active = Boolean(" in source
    assert "item === focusedItem || candidate" in source
    assert "setActive(item, active)" in source


def test_contact_copy_has_capability_check_fallback_and_live_feedback(client):
    source = (JS / "contact.js").read_text()
    html = client.get("/contact").get_data(as_text=True)

    assert "navigator.clipboard" in source
    assert 'typeof navigator.clipboard.writeText === "function"' in source
    assert "Email ready to copy manually" in source
    assert "Email copied." in source
    assert 'aria-live="polite"' in html
    assert "contact.js" in html


def test_pages_load_their_interaction_scripts(client):
    home = client.get("/").get_data(as_text=True)
    contact = client.get("/contact").get_data(as_text=True)

    assert "navigation.js" in home
    assert "constellation.js" in home
    assert "section-tracker.js" in home
    assert "contact.js" in contact
