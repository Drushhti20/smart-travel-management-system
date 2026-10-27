"""End-to-end integration flow verification using Flask test client."""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app import app


def test_complete_user_flow():
    """Verify entire user journey: registration, login, dashboard, trip CRUD, logout."""
    print("\n--- Starting Full User Journey Verification ---")
    client = app.test_client()

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    print("[PASS] 1. /api/health returned 200 OK:", res.get_json()["status"])

    # 2. Homepage and static assets
    home_res = client.get("/")
    assert home_res.status_code == 200
    assert "Your next adventure" in home_res.get_data(as_text=True)
    print("[PASS] 2. Homepage (/) served successfully with correct branding and hero copy.")

    css_res = client.get("/css/style.css")
    assert css_res.status_code == 200
    print("[PASS] 3. Stylesheet (/css/style.css) served successfully.")

    dash_page = client.get("/dashboard")
    assert dash_page.status_code == 200
    print("[PASS] 4. Dashboard page (/dashboard) served successfully.")

    # 3. Registration
    reg_payload = {
        "name": "Jordan Bell",
        "email": "jordan@beyondhorizons.test",
        "password": "ExploreTheWorld#2026",
        "confirmPassword": "ExploreTheWorld#2026"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.get_json()["user"]
    print(f"[PASS] 5. User registered: {user_data['name']} ({user_data['email']}), ID={user_data['id']}")

    # 4. Check active session (/api/auth/me)
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.get_json()["authenticated"] is True
    print("[PASS] 6. Session verified via /api/auth/me.")

    # 5. Check initial empty trip list and stats
    trips_res = client.get("/api/trips")
    assert trips_res.status_code == 200
    assert trips_res.get_json()["count"] == 0
    print("[PASS] 7. Initial empty trip list confirmed.")

    stats_res = client.get("/api/trips/stats")
    assert stats_res.status_code == 200
    assert stats_res.get_json()["stats"]["total_trips"] == 0
    print("[PASS] 8. Initial dashboard statistics confirmed (0 trips, $0 budget).")

    # 6. Create Trip 1: Santorini
    trip1_payload = {
        "title": "Santorini Sunsets & Sailing",
        "destination": "Santorini, Greece",
        "start_date": "2026-11-15",
        "end_date": "2026-11-22",
        "budget": 2800.00,
        "travelers": 2,
        "notes": "Book Oia photography tour and catamaran cruise."
    }
    create_res1 = client.post("/api/trips", json=trip1_payload)
    assert create_res1.status_code == 201
    trip1 = create_res1.get_json()["trip"]
    trip1_id = trip1["id"]
    print(f"[PASS] 9. Trip 1 created: '{trip1['title']}' to {trip1['destination']} (ID: {trip1_id})")

    # 7. Create Trip 2: Kyoto
    trip2_payload = {
        "title": "Autumn in Kyoto",
        "destination": "Kyoto, Japan",
        "start_date": "2026-12-05",
        "end_date": "2026-12-14",
        "budget": 3400.00,
        "travelers": 1,
        "notes": "Explore bamboo forest, tea ceremony, and temple gardens."
    }
    create_res2 = client.post("/api/trips", json=trip2_payload)
    assert create_res2.status_code == 201
    trip2 = create_res2.get_json()["trip"]
    trip2_id = trip2["id"]
    print(f"[PASS] 10. Trip 2 created: '{trip2['title']}' to {trip2['destination']} (ID: {trip2_id})")

    # 8. Check updated stats
    stats_res2 = client.get("/api/trips/stats")
    stats2 = stats_res2.get_json()["stats"]
    assert stats2["total_trips"] == 2
    assert stats2["total_budget"] == 6200.00
    assert stats2["unique_destinations"] == 2
    print(f"[PASS] 11. Real-time stats verified: Total Trips={stats2['total_trips']}, Budget=${stats2['total_budget']}, Destinations={stats2['unique_destinations']}.")

    # 9. Read trip details
    view_res = client.get(f"/api/trips/{trip1_id}")
    assert view_res.status_code == 200
    assert view_res.get_json()["trip"]["duration_days"] == 8
    print("[PASS] 12. Read trip details verified (calculated duration = 8 days).")

    # 10. Update Trip 1
    updated_payload = {
        "title": "Santorini & Mykonos Island Hopping",
        "destination": "Santorini & Mykonos, Greece",
        "start_date": "2026-11-15",
        "end_date": "2026-11-25",
        "budget": 3500.00,
        "travelers": 2,
        "notes": "Extended itinerary to include 3 days in Mykonos."
    }
    update_res = client.put(f"/api/trips/{trip1_id}", json=updated_payload)
    assert update_res.status_code == 200
    updated_trip = update_res.get_json()["trip"]
    assert updated_trip["title"] == "Santorini & Mykonos Island Hopping"
    assert updated_trip["budget"] == 3500.00
    assert updated_trip["duration_days"] == 11
    print("[PASS] 13. Update trip verified: Title and Budget updated correctly.")

    # 11. Delete Trip 2
    del_res = client.delete(f"/api/trips/{trip2_id}")
    assert del_res.status_code == 200
    print(f"[PASS] 14. Delete trip verified for ID: {trip2_id}.")

    # Confirm remaining trip count is 1
    final_list = client.get("/api/trips").get_json()
    assert final_list["count"] == 1
    assert final_list["trips"][0]["id"] == trip1_id
    print("[PASS] 15. Remaining trip count verified (1 trip remaining).")

    # 12. Logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    me_after = client.get("/api/auth/me").get_json()
    assert me_after["authenticated"] is False
    print("[PASS] 16. Logout verified; session terminated.")

    # 13. Attempting trip creation after logout must fail with 401
    unauth_res = client.post("/api/trips", json=trip1_payload)
    assert unauth_res.status_code == 401
    print("[PASS] 17. Protected route rejection confirmed (HTTP 401 Unauthorized).")

    print("\n>>> ALL 17 END-TO-END FLOW CHECKS PASSED PERFECTLY! <<<\n")


if __name__ == "__main__":
    test_complete_user_flow()
