"""
test_api.py – SaFi Njema Python Backend Test Suite
Run: pytest test_api.py -v
Requires: pip install httpx pytest pytest-asyncio
"""
import datetime
import time
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Set test environment BEFORE importing app
import os
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only_not_production")
os.environ.setdefault("SMTP_PASS", "")  # Disable emails in tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/test_safinjema.db")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminTest123!")

from main import app

BASE = "/api"
TS = int(time.time())  # unique suffix per test run


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Shared state across tests ─────────────────────────────────
state = {}


# ═══════════════════════════════════
# HEALTH
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_health(client):
    r = await client.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert "FastAPI" in r.json()["framework"]


@pytest.mark.asyncio
async def test_api_root(client):
    r = await client.get(f"{BASE}/")
    assert r.status_code == 200
    assert "endpoints" in r.json()


# ═══════════════════════════════════
# AUTH – REGISTER
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_register_success(client):
    r = await client.post(f"{BASE}/auth/register", json={
        "name": "Test User",
        "email": f"test{TS}@safinjema.test",
        "phone": "+27710000001",
        "password": "TestPass123!",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["token"]
    assert data["user"]["email"] == f"test{TS}@safinjema.test"
    state["token"] = data["token"]
    state["email"] = data["user"]["email"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    r = await client.post(f"{BASE}/auth/register", json={
        "name": "Dup", "email": state["email"],
        "password": "TestPass123!",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client):
    r = await client.post(f"{BASE}/auth/register", json={
        "name": "X", "email": f"x{TS}@test.com", "password": "123",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    r = await client.post(f"{BASE}/auth/register", json={
        "name": "X", "email": "notanemail", "password": "TestPass123!",
    })
    assert r.status_code == 422


# ═══════════════════════════════════
# AUTH – LOGIN
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_login_success(client):
    r = await client.post(f"{BASE}/auth/login", json={
        "email": state["email"], "password": "TestPass123!",
    })
    assert r.status_code == 200
    assert r.json()["token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    r = await client.post(f"{BASE}/auth/login", json={
        "email": state["email"], "password": "wrongpassword",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    r = await client.post(f"{BASE}/auth/login", json={
        "email": "nobody@nowhere.com", "password": "whatever",
    })
    assert r.status_code == 401


# ═══════════════════════════════════
# AUTH – PROFILE / ME
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_get_me(client):
    r = await client.get(f"{BASE}/auth/me",
                         headers={"Authorization": f"Bearer {state['token']}"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == state["email"]


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    r = await client.get(f"{BASE}/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client):
    r = await client.put(f"{BASE}/auth/profile",
                         headers={"Authorization": f"Bearer {state['token']}"},
                         json={"name": "Updated Name", "phone": "+27720000000"})
    assert r.status_code == 200
    assert r.json()["user"]["name"] == "Updated Name"


# ═══════════════════════════════════
# AUTH – ADMIN LOGIN
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_admin_login(client):
    r = await client.post(f"{BASE}/auth/login", json={
        "email": os.environ["ADMIN_EMAIL"],
        "password": os.environ["ADMIN_PASSWORD"],
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["role"] == "admin"
    state["admin_token"] = data["token"]


# ═══════════════════════════════════
# AUTH – PASSWORD RESET
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_forgot_password_always_200(client):
    r = await client.post(f"{BASE}/auth/forgot-password",
                          json={"email": state["email"]})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_200(client):
    r = await client.post(f"{BASE}/auth/forgot-password",
                          json={"email": "nobody@nowhere.com"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    r = await client.post(f"{BASE}/auth/reset-password",
                          json={"token": "fake_token_xyz", "new_password": "NewPass123!"})
    assert r.status_code == 400


# ═══════════════════════════════════
# BOOKINGS
# ═══════════════════════════════════
tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()


@pytest.mark.asyncio
async def test_create_booking(client):
    r = await client.post(f"{BASE}/bookings", json={
        "name": "Booking Client", "email": f"client{TS}@test.com",
        "phone": "+27710000002", "service": "Carpet Cleaning",
        "date": tomorrow, "time": "9:00 AM", "area": "Claremont",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["booking_ref"].startswith("SN-")
    state["booking_ref"] = data["booking_ref"]


@pytest.mark.asyncio
async def test_create_booking_missing_fields(client):
    r = await client.post(f"{BASE}/bookings", json={"name": "Incomplete"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_booking_past_date(client):
    r = await client.post(f"{BASE}/bookings", json={
        "name": "Test", "email": "t@t.com", "phone": "+27700000000",
        "service": "Carpet Cleaning", "date": "2020-01-01", "time": "9:00 AM",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_booking_invalid_service(client):
    r = await client.post(f"{BASE}/bookings", json={
        "name": "Test", "email": "t@t.com", "phone": "+27700000000",
        "service": "Fake Service XYZ", "date": tomorrow, "time": "9:00 AM",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_my_bookings(client):
    r = await client.get(f"{BASE}/bookings/my",
                         headers={"Authorization": f"Bearer {state['token']}"})
    assert r.status_code == 200
    assert isinstance(r.json()["bookings"], list)


@pytest.mark.asyncio
async def test_get_my_bookings_no_auth(client):
    r = await client.get(f"{BASE}/bookings/my")
    assert r.status_code == 401


# ═══════════════════════════════════
# CONTACT
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_contact_form(client):
    r = await client.post(f"{BASE}/contact", json={
        "name": "Contact Tester",
        "email": f"contact{TS}@test.com",
        "message": "I need a quote for office cleaning.",
    })
    assert r.status_code == 201
    assert r.json()["success"] is True


@pytest.mark.asyncio
async def test_contact_missing_message(client):
    r = await client.post(f"{BASE}/contact", json={
        "name": "Test", "email": "test@test.com",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_contact_invalid_email(client):
    r = await client.post(f"{BASE}/contact", json={
        "name": "Test", "email": "notanemail", "message": "Hello",
    })
    assert r.status_code == 422


# ═══════════════════════════════════
# QUOTES / PRICING
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_list_services(client):
    r = await client.get(f"{BASE}/quotes/services")
    assert r.status_code == 200
    assert len(r.json()["services"]) > 0


@pytest.mark.asyncio
async def test_get_service_by_id(client):
    r = await client.get(f"{BASE}/quotes/services/carpet")
    assert r.status_code == 200
    assert r.json()["service"]["id"] == "carpet"


@pytest.mark.asyncio
async def test_get_service_not_found(client):
    r = await client.get(f"{BASE}/quotes/services/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_estimate(client):
    r = await client.get(f"{BASE}/quotes/estimate/mattress")
    assert r.status_code == 200
    assert "pricing" in r.json()


@pytest.mark.asyncio
async def test_submit_quote(client):
    r = await client.post(f"{BASE}/quotes", json={
        "name": "Quote Tester",
        "email": f"quote{TS}@test.com",
        "service": "Carpet Cleaning",
        "property_type": "Apartment",
    })
    assert r.status_code == 201
    assert r.json()["quote_id"]


# ═══════════════════════════════════
# ADMIN
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_admin_dashboard(client):
    r = await client.get(f"{BASE}/admin/dashboard",
                         headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert r.status_code == 200
    data = r.json()
    assert "stats" in data
    assert "bookings" in data["stats"]


@pytest.mark.asyncio
async def test_admin_list_bookings(client):
    r = await client.get(f"{BASE}/admin/bookings",
                         headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert r.status_code == 200
    assert isinstance(r.json()["bookings"], list)


@pytest.mark.asyncio
async def test_admin_bookings_filter_status(client):
    r = await client.get(f"{BASE}/admin/bookings?status=pending",
                         headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_admin_list_messages(client):
    r = await client.get(f"{BASE}/admin/messages",
                         headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_admin_list_users(client):
    r = await client.get(f"{BASE}/admin/users",
                         headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert r.status_code == 200
    assert isinstance(r.json()["users"], list)


@pytest.mark.asyncio
async def test_admin_audit_log(client):
    r = await client.get(f"{BASE}/admin/audit",
                         headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert r.status_code == 200
    assert isinstance(r.json()["logs"], list)


@pytest.mark.asyncio
async def test_admin_route_blocked_for_customer(client):
    r = await client.get(f"{BASE}/admin/dashboard",
                         headers={"Authorization": f"Bearer {state['token']}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_route_blocked_no_auth(client):
    r = await client.get(f"{BASE}/admin/dashboard")
    assert r.status_code == 401


# ═══════════════════════════════════
# SECURITY
# ═══════════════════════════════════
@pytest.mark.asyncio
async def test_invalid_jwt_returns_401(client):
    r = await client.get(f"{BASE}/auth/me",
                         headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client):
    r = await client.get(f"{BASE}/nonexistent-route-xyz")
    assert r.status_code == 404


# Cleanup test DB
def pytest_sessionfinish(session, exitstatus):
    import os
    test_db = "data/test_safinjema.db"
    if os.path.exists(test_db):
        os.remove(test_db)
