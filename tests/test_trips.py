"""Tests for Trip CRUD Operations and Validation."""


def test_create_and_read_trip(auth, client):
    """Test creating a trip and reading it back."""
    auth.register("Sara Connor", "sara@example.com", "TravelPro2026")

    trip_payload = {
        "title": "Santorini Sunset Voyage",
        "destination": "Santorini, Greece",
        "start_date": "2026-11-10",
        "end_date": "2026-11-18",
        "budget": 2400.50,
        "travelers": 2,
        "notes": "Book caldera boat tour and Oia photography session."
    }

    create_res = client.post("/api/trips", json=trip_payload)
    assert create_res.status_code == 201
    created_data = create_res.get_json()
    assert created_data["success"] is True
    trip = created_data["trip"]
    assert trip["title"] == "Santorini Sunset Voyage"
    assert trip["destination"] == "Santorini, Greece"
    assert trip["budget"] == 2400.50
    assert trip["travelers"] == 2
    assert trip["duration_days"] == 9
    assert trip["status"] == "Upcoming"
    trip_id = trip["id"]

    # Read back single trip
    get_res = client.get(f"/api/trips/{trip_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["trip"]["title"] == "Santorini Sunset Voyage"

    # List trips
    list_res = client.get("/api/trips")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert list_data["count"] == 1
    assert list_data["trips"][0]["id"] == trip_id


def test_update_trip(auth, client):
    """Test updating an existing trip."""
    auth.register("Kenji Sato", "kenji@example.com", "KyotoTravel88")

    # Create trip
    create_res = client.post("/api/trips", json={
        "title": "Kyoto Temples Tour",
        "destination": "Kyoto, Japan",
        "start_date": "2026-12-01",
        "end_date": "2026-12-07",
        "budget": 1800.0,
        "travelers": 1,
        "notes": "Visit Fushimi Inari and Arashiyama."
    })
    trip_id = create_res.get_json()["trip"]["id"]

    # Update trip
    update_res = client.put(f"/api/trips/{trip_id}", json={
        "title": "Kyoto & Nara Cultural Trek",
        "destination": "Kyoto and Nara, Japan",
        "start_date": "2026-12-01",
        "end_date": "2026-12-10",
        "budget": 2200.0,
        "travelers": 2,
        "notes": "Extended to include Nara deer park and traditional tea ceremony."
    })
    assert update_res.status_code == 200
    updated_trip = update_res.get_json()["trip"]
    assert updated_trip["title"] == "Kyoto & Nara Cultural Trek"
    assert updated_trip["destination"] == "Kyoto and Nara, Japan"
    assert updated_trip["budget"] == 2200.0
    assert updated_trip["travelers"] == 2
    assert updated_trip["duration_days"] == 10


def test_delete_trip(auth, client):
    """Test deleting an existing trip."""
    auth.register("Marco Polo", "marco@example.com", "SilkRoad2026")

    create_res = client.post("/api/trips", json={
        "title": "Swiss Alps Hiking",
        "destination": "Zermatt, Switzerland",
        "start_date": "2026-11-05",
        "end_date": "2026-11-12",
        "budget": 3100.0,
        "travelers": 2,
        "notes": "Matterhorn view trail."
    })
    trip_id = create_res.get_json()["trip"]["id"]

    # Delete
    del_res = client.delete(f"/api/trips/{trip_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # Verify deleted
    get_res = client.get(f"/api/trips/{trip_id}")
    assert get_res.status_code == 404

    # List trips should now be empty
    list_res = client.get("/api/trips")
    assert list_res.get_json()["count"] == 0


def test_trip_validation_errors(auth, client):
    """Test validation errors for invalid dates, budget, travelers, etc."""
    auth.register("Tester Bob", "bob@example.com", "TestingPass123")

    # Reversed dates: end_date before start_date
    res1 = client.post("/api/trips", json={
        "title": "Invalid Trip Dates",
        "destination": "Paris, France",
        "start_date": "2026-12-15",
        "end_date": "2026-12-10",
        "budget": 1000,
        "travelers": 1
    })
    assert res1.status_code == 400
    assert "earlier than start date" in res1.get_json()["message"].lower()

    # Negative budget
    res2 = client.post("/api/trips", json={
        "title": "Negative Budget Trip",
        "destination": "Rome, Italy",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "budget": -500,
        "travelers": 1
    })
    assert res2.status_code == 400
    assert "cannot be negative" in res2.get_json()["message"].lower()

    # Travelers less than 1
    res3 = client.post("/api/trips", json={
        "title": "Zero Travelers Trip",
        "destination": "Rome, Italy",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "budget": 500,
        "travelers": 0
    })
    assert res3.status_code == 400
    assert "at least 1" in res3.get_json()["message"].lower()

    # Missing title
    res4 = client.post("/api/trips", json={
        "title": "",
        "destination": "Rome, Italy",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "budget": 500,
        "travelers": 1
    })
    assert res4.status_code == 400
    assert "title must be" in res4.get_json()["message"].lower()


def test_dashboard_stats(auth, client):
    """Test dashboard real aggregate statistics calculation."""
    auth.register("Stat Collector", "stats@example.com", "StatMaster77")

    # Check empty stats
    empty_stats = client.get("/api/trips/stats").get_json()["stats"]
    assert empty_stats["total_trips"] == 0
    assert empty_stats["total_budget"] == 0
    assert empty_stats["upcoming_trips"] == 0

    # Add two trips
    client.post("/api/trips", json={
        "title": "Bali Retreat",
        "destination": "Bali, Indonesia",
        "start_date": "2026-11-15",
        "end_date": "2026-11-22",
        "budget": 1500,
        "travelers": 2
    })
    client.post("/api/trips", json={
        "title": "Tokyo Food Journey",
        "destination": "Tokyo, Japan",
        "start_date": "2026-12-10",
        "end_date": "2026-12-20",
        "budget": 2500,
        "travelers": 3
    })

    stats_res = client.get("/api/trips/stats")
    assert stats_res.status_code == 200
    stats = stats_res.get_json()["stats"]
    assert stats["total_trips"] == 2
    assert stats["total_budget"] == 4000.0
    assert stats["unique_destinations"] == 2
    assert stats["upcoming_trips"] == 2
    assert stats["next_trip"]["destination"] == "Bali, Indonesia"


def test_update_trip_with_iso_dates_and_travellers_spelling(auth, client):
    """
    Test updating a trip when dates contain ISO timestamp (e.g. from MongoDB/API)
    and field names use alternative spelling (travellers, startDate, endDate).
    """
    auth.register("Dev Tester", "devtester@example.com", "TestingPassword#2026")

    # Create trip
    create_res = client.post("/api/trips", json={
        "title": "Initial Trip",
        "destination": "London, UK",
        "start_date": "2026-11-10",
        "end_date": "2026-11-15",
        "budget": 1200,
        "travelers": 1
    })
    trip_id = create_res.get_json()["trip"]["id"]

    # Update with ISO timestamp strings and alternate keys
    update_res = client.put(f"/api/trips/{trip_id}", json={
        "title": "Updated London Tour",
        "destination": "London & Oxford, UK",
        "startDate": "2026-11-10T00:00:00Z",
        "endDate": "2026-11-18T00:00:00Z",
        "budget": 1650.0,
        "travellers": 2,
        "notes": "Added day trip to Oxford University."
    })
    assert update_res.status_code == 200
    updated = update_res.get_json()["trip"]
    assert updated["title"] == "Updated London Tour"
    assert updated["destination"] == "London & Oxford, UK"
    assert updated["start_date"] == "2026-11-10"
    assert updated["end_date"] == "2026-11-18"
    assert updated["travelers"] == 2
    assert updated["duration_days"] == 9


def test_update_trip_invalid_ids(auth, client):
    """Test updating with malformed or non-existent trip IDs."""
    auth.register("ID Tester", "idtester@example.com", "TestingPassword#2026")

    # Malformed ID
    res1 = client.put("/api/trips/not-a-valid-object-id", json={
        "title": "Test",
        "destination": "Test",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "budget": 100,
        "travelers": 1
    })
    assert res1.status_code == 400

    # Non-existent 24-character hex ID
    res2 = client.put("/api/trips/507f1f77bcf86cd799439011", json={
        "title": "Test",
        "destination": "Test",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "budget": 100,
        "travelers": 1
    })
    assert res2.status_code == 404
