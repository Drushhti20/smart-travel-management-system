"""Tests for Authentication and User Registration."""


def test_register_success(auth, client):
    """Test successful user registration."""
    res = auth.register("Maya Lin", "maya@example.com", "SecretPass123")
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["name"] == "Maya Lin"
    assert data["user"]["email"] == "maya@example.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Session check via /api/auth/me
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    me_data = me_res.get_json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["email"] == "maya@example.com"


def test_register_duplicate_email(auth):
    """Test duplicate registration is rejected with 409 Conflict."""
    res1 = auth.register("First User", "duplicate@example.com", "Password123")
    assert res1.status_code == 201

    res2 = auth.register("Second User", "duplicate@example.com", "Password456")
    assert res2.status_code == 409
    data = res2.get_json()
    assert data["success"] is False
    assert "already exists" in data["message"].lower()


def test_register_validation_errors(auth):
    """Test various registration validation rules."""
    # Short name
    res = auth.register("M", "valid@example.com", "Password123")
    assert res.status_code == 400
    assert "between 2 and 80" in res.get_json()["message"]

    # Invalid email
    res = auth.register("Valid Name", "not-an-email", "Password123")
    assert res.status_code == 400
    assert "valid email" in res.get_json()["message"].lower()

    # Short password
    res = auth.register("Valid Name", "valid@example.com", "short")
    assert res.status_code == 400
    assert "at least 8" in res.get_json()["message"].lower()

    # Mismatched passwords
    res = auth.register("Valid Name", "valid@example.com", "Password123", confirm="Different123")
    assert res.status_code == 400
    assert "do not match" in res.get_json()["message"].lower()


def test_login_success(auth, client):
    """Test login with correct credentials."""
    auth.register("Rohan Mehra", "rohan@example.com", "Adventure2026")
    auth.logout()

    res = auth.login("rohan@example.com", "Adventure2026")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["name"] == "Rohan Mehra"

    # Confirm session is valid
    me_res = client.get("/api/auth/me")
    assert me_res.get_json()["authenticated"] is True


def test_login_invalid_credentials(auth):
    """Test login fails with incorrect password or unknown user."""
    auth.register("Rohan Mehra", "rohan@example.com", "Adventure2026")
    auth.logout()

    # Wrong password
    res = auth.login("rohan@example.com", "WrongPassword999")
    assert res.status_code == 401
    assert res.get_json()["success"] is False

    # Unknown email
    res2 = auth.login("nonexistent@example.com", "Adventure2026")
    assert res2.status_code == 401
    assert res2.get_json()["success"] is False


def test_logout(auth, client):
    """Test logout clears session."""
    auth.register("Elena Rostova", "elena@example.com", "HorizonVoyage99")
    assert client.get("/api/auth/me").get_json()["authenticated"] is True

    res = auth.logout()
    assert res.status_code == 200
    assert client.get("/api/auth/me").get_json()["authenticated"] is False
