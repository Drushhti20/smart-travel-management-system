"""Security, Authorization, and Data Isolation Tests."""
from backend.database import get_db, close_db


def test_unauthenticated_protected_routes(client):
    """Test accessing protected endpoints without an active session returns 401."""
    endpoints = [
        ("GET", "/api/trips"),
        ("POST", "/api/trips"),
        ("GET", "/api/trips/stats"),
        ("GET", "/api/trips/507f1f77bcf86cd799439011"),
        ("PUT", "/api/trips/507f1f77bcf86cd799439011"),
        ("DELETE", "/api/trips/507f1f77bcf86cd799439011"),
    ]

    for method, url in endpoints:
        if method == "GET":
            res = client.get(url)
        elif method == "POST":
            res = client.post(url, json={})
        elif method == "PUT":
            res = client.put(url, json={})
        elif method == "DELETE":
            res = client.delete(url)
        assert res.status_code == 401
        assert res.get_json()["success"] is False
        assert "Authentication required" in res.get_json()["message"]


def test_cross_user_trip_isolation(auth, client):
    """
    Test that trips belonging to User A cannot be viewed, updated,
    or deleted by User B.
    """
    # 1. Register User A and create a trip
    auth.register("Alice Wonderland", "alice@example.com", "PasswordAlice123")
    create_res = client.post("/api/trips", json={
        "title": "Alice Secret Trip",
        "destination": "Oxford, UK",
        "start_date": "2026-11-20",
        "end_date": "2026-11-25",
        "budget": 1200,
        "travelers": 1,
        "notes": "Private itinerary"
    })
    alice_trip_id = create_res.get_json()["trip"]["id"]

    # 2. Logout User A
    auth.logout()

    # 3. Register User B
    auth.register("Bob Builder", "bob@example.com", "PasswordBob123")

    # Bob's trips list should NOT contain Alice's trip
    bobs_trips = client.get("/api/trips").get_json()["trips"]
    assert len(bobs_trips) == 0

    # Bob cannot GET Alice's trip by ID
    get_res = client.get(f"/api/trips/{alice_trip_id}")
    assert get_res.status_code == 404

    # Bob cannot UPDATE Alice's trip
    update_res = client.put(f"/api/trips/{alice_trip_id}", json={
        "title": "Hacked Trip Title",
        "destination": "Nowhere",
        "start_date": "2026-11-20",
        "end_date": "2026-11-25",
        "budget": 500,
        "travelers": 1
    })
    assert update_res.status_code == 404

    # Bob cannot DELETE Alice's trip
    delete_res = client.delete(f"/api/trips/{alice_trip_id}")
    assert delete_res.status_code == 404

    # 4. Log back in as Alice and confirm trip remains untouched
    auth.logout()
    auth.login("alice@example.com", "PasswordAlice123")
    alice_res = client.get(f"/api/trips/{alice_trip_id}")
    assert alice_res.status_code == 200
    assert alice_res.get_json()["trip"]["title"] == "Alice Secret Trip"


def test_passwords_are_securely_hashed(auth):
    """Test that passwords stored in the database are hashed and never plain text."""
    raw_password = "MySuperSecretPlainPassword#2026"
    auth.register("Secured User", "secure@example.com", raw_password)

    db = get_db()
    user_in_db = db.users.find_one({"email": "secure@example.com"})
    assert user_in_db is not None
    assert "password_hash" in user_in_db
    assert user_in_db["password_hash"] != raw_password
    # Check that it's a werkzeug hash (e.g. scrypt: or pbkdf2:)
    assert user_in_db["password_hash"].startswith(("scrypt:", "pbkdf2:"))


def test_database_connection_failure_handling(auth):
    """Test that the application handles database unavailability gracefully."""
    # Temporarily close the database connection
    close_db()

    # Attempting to register when DB is offline returns 503 Service Unavailable
    res = auth.register("Offline User", "offline@example.com", "Password123")
    assert res.status_code == 503
    assert "not ready" in res.get_json()["message"].lower()
