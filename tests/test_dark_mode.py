"""Tests for STORY-013: Dark Mode — no-flash pre-render script in <head>"""


def test_base_has_dark_mode_prerender_script(client):
    """The login page (no auth needed) should contain the no-flash dark mode init in <head>."""
    r = client.get("/login")
    assert r.status_code == 200
    html = r.text
    # Script must appear before </head> and apply 'dark' class to <html>
    head_end = html.lower().index("</head>")
    head_section = html[:head_end]
    assert "localstorage" in head_section.lower()
    assert "dark" in head_section.lower()


def test_dark_mode_toggle_script_present(client):
    """toggleDarkMode JS function must exist in the page."""
    r = client.get("/login")
    assert "toggleDarkMode" in r.text or "toggledarkmode" in r.text.lower()
