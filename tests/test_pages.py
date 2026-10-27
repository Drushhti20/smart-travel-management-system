"""Tests for Frontend Page Serving and Static Assets."""


def test_home_page_serving(client):
    """Test that the homepage is served correctly with key text and structure."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Your next adventure" in html
    assert "starts here." in html
    assert "How It Works" in html
    assert "Create your account" in html
    assert "Add your travel plans" in html
    assert "Manage and update your trips" in html
    assert "BEYOND" in html
    assert "HORIZONS" in html


def test_login_page_serving(client):
    """Test that the login page matches the reference design and text."""
    res = client.get("/login")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Welcome back" in html
    assert "LET'S GET YOU THERE" in html
    assert "WELCOME BACK, EXPLORER" in html
    assert "closer than ever." in html
    assert "login-form" in html
    assert "Sign in" in html
    assert "The world is yours to explore." in html


def test_register_page_serving(client):
    """Test that the registration page matches the reference design and text."""
    res = client.get("/register")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Create your account" in html
    assert "JOIN THE JOURNEY" in html
    assert "YOUR NEXT STORY STARTS HERE" in html
    assert "waiting for" in html
    assert "register-form" in html
    assert "Discover more. Travel further. Go beyond." in html


def test_dashboard_page_serving(client):
    """Test that the dashboard HTML structure is served correctly."""
    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "My Trips" in html
    assert "stat-total-trips" in html
    assert "modal-create-trip" in html
    assert "modal-edit-trip" in html
    assert "modal-view-trip" in html
    assert "modal-delete-confirm" in html


def test_static_assets_serving(client):
    """Test that static CSS and JavaScript files are served correctly."""
    css_res = client.get("/css/style.css")
    assert css_res.status_code == 200
    assert "var(--gradient-btn)" in css_res.get_data(as_text=True)

    script_res = client.get("/js/script.js")
    assert script_res.status_code == 200

    auth_res = client.get("/js/auth.js")
    assert auth_res.status_code == 200

    dash_res = client.get("/js/dashboard.js")
    assert dash_res.status_code == 200


def test_health_endpoint(client):
    """Test API health check returns healthy status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"]["ready"] is True
