# Beyond Horizons — Smart Travel Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-black.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MongoDB%20Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Tests](https://img.shields.io/badge/Tests-24%20Passed%20(100%25)-brightgreen.svg)]()
[![Design](https://img.shields.io/badge/UI%2FUX-Unified%20Glassmorphism-cyan.svg)]()

**Beyond Horizons** is a premium, full-stack travel management web application engineered for college PBL (Project-Based Learning). It provides travelers with an intuitive personal workspace to plan journeys, track budgets, schedule itineraries, and manage trips across an elegant, responsive interface.

---

## 1. Project Overview & Visual Design System

The application features a unified aesthetic directly inspired by the official Beyond Horizons design system:

- **Color Palette:**
  - Deep midnight navy (`#0f172a`, `#1e293b`) for typography and card headers.
  - Electric blue (`#0284c7`) to bright cyan (`#38bdf8`, `#00b0ff`) gradient for primary buttons, active highlights, and arrow accents.
  - Soft, pale blue-grey background (`#f1f5f9`, `#eef4f8`) with frosted landscape backdrop.
  - Crisp white content cards (`#ffffff`) with generous padding, `28px` rounded corners, and refined elevation shadows (`0 20px 60px rgba(15, 23, 42, 0.08)`).
- **Typography:** Modern typography featuring **Manrope** for bold display headings and **Inter** for clean UI readability.
- **Visual Composition:** Split-screen layouts with cinematic travel photography (mountains, coastlines, waterfalls) paired with dark gradient text overlays for readability.

---

## 2. Core Pages & Capabilities

```
   [ Homepage ] ──────> [ Split-Screen Auth ] ──────> [ Personal Dashboard ]
(Hero, 3 Steps,             (Register / Login with            (Real Stats, Search Filter,
  4 Core Features)           Hashed Passwords)                Trip Grid, Modals & Toast)
                                                                 │
                                ┌────────────────────────────────┴────────────────────────────────┐
                                ▼                                ▼                                ▼
                        [ Create Journey ]               [ View / Edit ]                  [ Delete Trip ]
                       (Dates, Budget, Notes)           (Full Details & Days)            (Modal Confirmation)
```

### A. Home Page (`frontend/html/index.html`)
- **Brand Navigation:** `▲ BEYOND HORIZONS` brand, Home, How It Works, Features, Sign In, and Create Account button. When logged in, dynamically updates navigation to point to Dashboard.
- **Hero Card:** Floating card with mountain lake scenery, headline *"Your next adventure starts here."*, subtitle, and *"Start Planning →"* gradient button.
- **How It Works (3 Steps):**
  1. *Create your account* — Sign up with your email to unlock your personal workspace.
  2. *Add your travel plans* — Enter destination, departure/return dates, budget, travelers, and notes.
  3. *Manage and update your trips* — Review itineraries, edit details, or remove finished journeys.
- **Core Capabilities (4 Cards):** Create & organize trips, View planned journeys, Edit trip details, and Manage trip info & status.

### B. Login Page (`frontend/html/login.html`)
- Direct visual match to Reference Screenshot 1:
  - Top-left page header with `▲ BEYOND HORIZONS`.
  - Floating rounded split card (`border-radius: 28px`).
  - Left panel: Mountain lake photo, overlay, `WELCOME BACK, EXPLORER`, headline *"Your next adventure is closer than ever."* (with `closer than ever.` in vibrant cyan), and `✦ The world is yours to explore.`.
  - Right panel: `← Back to home`, `LET'S GET YOU THERE`, `Welcome back`, email field, password field with `Show`/`Hide` toggle, full-width gradient `Sign in →` button, `New to Beyond Horizons? Create an account`, and `▣ Sign-in is handled by your project backend.` note.

### C. Registration Page (`frontend/html/register.html`)
- Direct visual match to Reference Screenshot 2:
  - Left panel: McWay Falls coastal cove photo, overlay, `YOUR NEXT STORY STARTS HERE`, headline *"The world is waiting for you."* (with `you.` in vibrant cyan), and `✦ Discover more. Travel further. Go beyond.`.
  - Right panel: `← Back to home`, `JOIN THE JOURNEY`, `Create your account`, full name, email, password with `Show` toggle, confirm password with `Show` toggle, agreement checkbox, gradient `Create account →` button, `Already have an account? Sign In`, and `▣ Your password is securely hashed before storage.` note.

### D. User Dashboard (`frontend/html/dashboard.html`)
- **Header:** Brand logo, greeting with the user's actual name (`Welcome back, [Name]!`), `+ Create New Trip` button, and `Sign Out ↗` button.
- **Welcome Banner:** Clean card greeting the user and presenting trip creation CTA.
- **Statistics Cards:** 4 real aggregate cards calculated directly from saved trips:
  1. *Total Trips*
  2. *Upcoming Trips*
  3. *Ongoing Trips*
  4. *Completed Trips*
- **My Trips Section:**
  - Real-time search by destination or title.
  - Dropdown filter by trip status (*All Statuses, Upcoming, Ongoing, Completed, Planned*).
  - Responsive trip cards with destination tag, title, status pill, dates, duration in days, budget, travelers count, notes preview, and `View`, `Edit`, `Delete` actions.
  - Illustrated empty state when 0 trips exist.
  - Comprehensive modal dialogs for Create, Edit, View, and Delete.
  - Floating toast notification system.

---

## 3. Critical Bug Fix: Trip Editing

### Root Cause Analysis
During investigation of the trip editing functionality, multiple root causes were identified:
1. **Date Format Incompatibility:** In `backend/services/trip_service.py`, `TripService.parse_date` strictly called `strptime("%Y-%m-%d")`. When dates came from MongoDB or datetime objects as ISO format strings (e.g. `2026-11-20T00:00:00` or `2026-11-20T00:00:00Z`), `strptime` threw a `ValueError` and returned `None`. This caused backend validation to reject valid update payloads with `"Please provide a valid start date (YYYY-MM-DD)."`.
2. **HTML5 `<input type="date">` Value Blanking:** In the frontend edit modal, when `trip.start_date` was populated with an ISO string containing time (`T00:00:00`), browsers adhering to the HTML5 specification reset the input's value to empty string `""`. Consequently, users saw blank date inputs or received validation errors on submission.
3. **MongoDB `user_id` Type Mismatch:** When updating a trip, the database query filtered strictly by `ObjectId(user_id)`. If documents had `user_id` stored as a string or vice versa, the update query matched 0 documents and returned HTTP 404.
4. **Field Name Variation:** Requests sending `travellers` (Commonwealth spelling) or camelCase dates (`startDate`, `endDate`) were ignored by the backend parser.
5. **Missing Event Listeners:** `edit-start-date` lacked a date change listener to synchronize the minimum allowed value of `edit-end-date`.

### How Trip Editing Now Works (End-to-End)
1. **User Action:** The user clicks **Edit** on a trip card (or inside the **View Details** modal).
2. **Pre-population:** `openEditTripModal(trip)` populates:
   - Trip ID: hidden input `#edit-trip-id`
   - Title & Destination: populated with existing values
   - Start & End Dates: normalized cleanly via `.split('T')[0].split(' ')[0]` into strict `YYYY-MM-DD` strings, ensuring browser date pickers display the existing dates correctly.
   - Budget & Travelers: cleanly parsed into numerical values.
   - Notes: populated with existing itinerary text.
   - Sets `edit-end-date.min = edit-start-date.value`.
3. **Submission & Client Validation:** When clicking **Save Changes**, `handleEditTripSubmit` validates required fields, verifies $End\ Date \ge Start\ Date$, and sends `PUT /api/trips/<trip_id>` with JSON credentials included.
4. **Backend Processing:**
   - `TripService.parse_date` safely splits timestamps (`T` or space) and parses standard dates.
   - `_build_user_filter` checks `user_id` against both `ObjectId` and `str` representations, ensuring data isolation without type mismatch failures.
   - MongoDB updates the document with `$set` and records `updated_at`.
5. **Persistence & Refresh:**
   - The backend returns the serialized updated trip with status 200.
   - The frontend immediately updates local state, updates the view modal if open, re-renders the grid, refreshes aggregate dashboard statistics, and triggers a success toast (`Trip "[Title]" updated successfully!`).
   - Changes persist permanently in the database across page refreshes and re-logins.

---

## 4. Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+) | Semantic HTML, modular CSS design system, event delegation |
| **Backend** | Python 3.10+, Flask 3.1+ | RESTful APIs, page rendering, session management |
| **Database** | MongoDB Atlas / PyMongo | Document storage with dual ObjectId/string query support |
| **Mock Fallback**| mongomock 4.1+ | Automatic in-memory storage when running offline or grading |
| **Security** | Werkzeug Security | `scrypt` / `pbkdf2` password hashing, `SameSite=Lax` cookies |
| **Testing** | Pytest 9.1+ | 24 automated unit, integration, and security tests |

---

## 5. Project Directory Structure

```text
smart-travel-management-system/
├── frontend/
│   ├── html/
│   │   ├── index.html          # Clean, modern landing page
│   │   ├── register.html       # Split-screen registration page
│   │   ├── login.html          # Split-screen login page
│   │   └── dashboard.html       # Personal travel dashboard & modals
│   ├── css/
│   │   ├── style.css           # Master design system & responsive styling
│   │   └── auth.css            # Stylesheet alias
│   ├── js/
│   │   ├── script.js           # Homepage navigation & active session detection
│   │   ├── auth.js             # Client validation, password toggles, API calls
│   │   └── dashboard.js        # Trip CRUD, real-time stats, filters, modals, toasts
│   └── assets/
│       └── images/             # Vector branding and local fallback assets
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration and environment variables
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py               # MongoDB Atlas connection & mongomock fallback
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py      # /api/auth (register, login, logout, me)
│   │   └── trip_routes.py      # /api/trips (CRUD + stats + user isolation)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Auth business logic & password hashing
│   │   └── trip_service.py     # Trip CRUD, date normalization, statistics
│   ├── app.py                  # Flask app factory, page routes, security headers
│   └── requirements.txt        # Python backend dependencies
├── tests/
│   ├── conftest.py             # Pytest fixtures and mock client setup
│   ├── test_auth.py            # Registration, login, logout, duplicate tests
│   ├── test_trips.py           # Trip CRUD, date validation, and stats tests
│   ├── test_security.py        # Protected routes, user isolation, hashing tests
│   ├── test_pages.py           # Page serving & static asset verification tests
│   ├── test_live_flow.py       # Full user journey integration test
│   └── run_tests.py            # Unified test suite runner
├── .env.example                # Root environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # Full documentation
```

---

## 6. How to Run the Application

### 1. Python Environment Setup

#### Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Start the Flask Server
```bash
python -m backend.app
```
*(Or `python backend/app.py`)*

### 4. Open in Your Browser
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Key URLs:
- **Home Page:** `http://127.0.0.1:5000/`
- **Login Page:** `http://127.0.0.1:5000/login`
- **Registration Page:** `http://127.0.0.1:5000/register`
- **Dashboard:** `http://127.0.0.1:5000/dashboard`
- **Health Check API:** `http://127.0.0.1:5000/api/health`

### 5. MongoDB Atlas Setup (Optional)
To connect to your cloud cluster, copy `.env.example` to `.env`:
```ini
SECRET_KEY=your-secure-random-secret-key-2026
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
DB_NAME=beyond_horizons
PORT=5000
FLASK_DEBUG=false
COOKIE_SECURE=false
```
*(If `MONGODB_URI` is omitted, the application runs on in-memory storage, allowing full demonstration and grading without cloud credentials).*

---

## 7. Automated Testing & Verification

Run the entire test suite:

```bash
python tests/run_tests.py
```

Or via pytest:
```bash
pytest tests/ -v
```

### Verified Test Suite Results (24 Passed, 0 Failed):
```text
============================= test session starts =============================
tests/test_auth.py::test_register_success PASSED                         [  4%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [  8%]
tests/test_auth.py::test_register_validation_errors PASSED               [ 12%]
tests/test_auth.py::test_login_success PASSED                            [ 16%]
tests/test_auth.py::test_login_invalid_credentials PASSED                [ 20%]
tests/test_auth.py::test_logout PASSED                                   [ 25%]
tests/test_live_flow.py::test_complete_user_flow PASSED                  [ 29%]
tests/test_pages.py::test_home_page_serving PASSED                       [ 33%]
tests/test_pages.py::test_login_page_serving PASSED                      [ 37%]
tests/test_pages.py::test_register_page_serving PASSED                   [ 41%]
tests/test_pages.py::test_dashboard_page_serving PASSED                  [ 45%]
tests/test_pages.py::test_static_assets_serving PASSED                   [ 50%]
tests/test_pages.py::test_health_endpoint PASSED                         [ 54%]
tests/test_security.py::test_unauthenticated_protected_routes PASSED     [ 58%]
tests/test_security.py::test_cross_user_trip_isolation PASSED            [ 62%]
tests/test_security.py::test_passwords_are_securely_hashed PASSED        [ 66%]
tests/test_security.py::test_database_connection_failure_handling PASSED [ 70%]
tests/test_trips.py::test_create_and_read_trip PASSED                    [ 75%]
tests/test_trips.py::test_update_trip PASSED                             [ 79%]
tests/test_trips.py::test_delete_trip PASSED                             [ 83%]
tests/test_trips.py::test_trip_validation_errors PASSED                  [ 87%]
tests/test_trips.py::test_dashboard_stats PASSED                         [ 91%]
tests/test_trips.py::test_update_trip_with_iso_dates_and_travellers_spelling PASSED [ 95%]
tests/test_trips.py::test_update_trip_invalid_ids PASSED                 [100%]
============================= 24 passed in 2.98s ==============================
```

---

## 8. Security & Data Protection Highlights

1. **User Data Isolation:** Every query on itineraries checks ownership using `user_id == session['user_id']`. Users cannot read, edit, or delete another user's trips.
2. **Password Security:** Cryptographic password hashing (`scrypt` / `pbkdf2:sha256`) via Werkzeug. Plain text passwords are never stored.
3. **Session Cookie Hardening:** Server-managed session cookies with `HttpOnly=True` and `SameSite=Lax`.
4. **Input Sanitization:** Both frontend and backend validate date order ($End\ Date \ge Start\ Date$), non-negative budgets, positive traveler counts, and escape HTML outputs.

---

## 9. License & PBL Credits

Developed for the **Beyond Horizons — Smart Travel Management System** College PBL Project (2026).
