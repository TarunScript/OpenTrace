import pytest
import pytest_asyncio
import httpx
from apps.api.app.main import app
from apps.api.app.database.session import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["supported_sites_count"] > 10


@pytest.mark.asyncio
async def test_sites_directory_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/sites")
        assert resp.status_code == 200
        sites = resp.json()
        assert len(sites) >= 20
        github = next((s for s in sites if s["name"] == "GitHub"), None)
        assert github is not None
        assert github["category"] == "developer"


@pytest.mark.asyncio
async def test_auth_workflow():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register
        reg_payload = {"email": "analyst@opentrace.org", "password": "SecurePassword123!"}
        reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_resp.status_code in (201, 400) # 400 if already registered from earlier test

        # 2. Login
        login_resp = await client.post("/api/v1/auth/login", json=reg_payload)
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        token = token_data["access_token"]

        # 3. Me
        me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "analyst@opentrace.org"


@pytest.mark.asyncio
async def test_create_and_query_investigation():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "type": "username",
            "value": "tarunkumar",
            "options": {"deep_search": False, "max_depth": 1},
        }
        create_resp = await client.post("/api/v1/investigations", json=payload)
        assert create_resp.status_code == 201
        inv = create_resp.json()
        assert "id" in inv
        assert inv["status"] in ("queued", "searching", "completed")
        assert inv["target_value"] == "tarunkumar"

        inv_id = inv["id"]

        # Get status
        status_resp = await client.get(f"/api/v1/investigations/{inv_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["id"] == inv_id

        # Get results
        results_resp = await client.get(f"/api/v1/investigations/{inv_id}/results")
        assert results_resp.status_code == 200
        res_data = results_resp.json()
        assert "profiles" in res_data
        assert "summary" in res_data


@pytest.mark.asyncio
async def test_investigation_ownership_and_authorization():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Register User A
        await client.post("/api/v1/auth/register", json={"email": "alice@domain.org", "password": "Password123!"})
        login_a = await client.post("/api/v1/auth/login", json={"email": "alice@domain.org", "password": "Password123!"})
        token_a = login_a.json()["access_token"]

        # Register User B
        await client.post("/api/v1/auth/register", json={"email": "bob@domain.org", "password": "Password123!"})
        login_b = await client.post("/api/v1/auth/login", json={"email": "bob@domain.org", "password": "Password123!"})
        token_b = login_b.json()["access_token"]

        # User A creates a private investigation
        inv_resp = await client.post(
            "/api/v1/investigations",
            json={"type": "username", "value": "alice_secret_target"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert inv_resp.status_code == 201
        alice_inv_id = inv_resp.json()["id"]

        # User B attempts to access User A's investigation -> Expect 403 Forbidden
        b_access = await client.get(
            f"/api/v1/investigations/{alice_inv_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert b_access.status_code == 403

        # Guest attempts to access User A's investigation -> Expect 403 Forbidden
        guest_access = await client.get(f"/api/v1/investigations/{alice_inv_id}")
        assert guest_access.status_code == 403

        # Guest lists investigations -> Must NOT contain Alice's investigation
        guest_list = await client.get("/api/v1/investigations")
        assert guest_list.status_code == 200
        guest_inv_ids = [item["id"] for item in guest_list.json()]
        assert alice_inv_id not in guest_inv_ids

        # User B attempts to delete User A's investigation -> Expect 403 Forbidden
        b_delete = await client.delete(
            f"/api/v1/investigations/{alice_inv_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert b_delete.status_code == 403

        # User A deletes their own investigation -> Expect 204 No Content
        a_delete = await client.delete(
            f"/api/v1/investigations/{alice_inv_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert a_delete.status_code == 204

        # Verify investigation is now soft-deleted (404)
        a_check = await client.get(
            f"/api/v1/investigations/{alice_inv_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert a_check.status_code == 404


@pytest.mark.asyncio
async def test_expired_and_invalid_jwt_tokens():
    from datetime import timedelta
    from apps.api.app.core.security import create_access_token
    from jose import jwt
    from apps.api.app.config import settings

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Expired token
        expired_token = create_access_token({"sub": "some_user_id"}, expires_delta=timedelta(minutes=-10))
        resp_expired = await client.get(
            "/api/v1/investigations",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp_expired.status_code == 401
        assert "expired" in resp_expired.json()["detail"].lower()

        # 2. Tampered signature token
        tampered_token = jwt.encode({"sub": "admin"}, "wrong_secret_key", algorithm="HS256")
        resp_tampered = await client.get(
            "/api/v1/investigations",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert resp_tampered.status_code == 401

        # 3. Malformed garbage token
        resp_garbage = await client.get(
            "/api/v1/investigations",
            headers={"Authorization": "Bearer this_is_not_a_valid_jwt"},
        )
        assert resp_garbage.status_code == 401


@pytest.mark.asyncio
async def test_password_hashing_security():
    from sqlalchemy import select
    from apps.api.app.database.session import AsyncSessionLocal
    from apps.api.app.models import User

    raw_password = "SuperSecretPassword99!"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "hashing_test@opentrace.org", "password": raw_password},
        )
        assert reg_resp.status_code in (201, 400)

    # Inspect directly in database
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "hashing_test@opentrace.org"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert raw_password not in user.password_hash
        assert user.password_hash.startswith("$2b$")  # Bcrypt signature


@pytest.mark.asyncio
async def test_error_handling_sanitization():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Malformed search input
        resp = await client.post("/api/v1/investigations", json={"type": "username", "value": ""})
        assert resp.status_code in (400, 422)
        # Verify no traceback is leaked
        text = resp.text
        assert "Traceback" not in text
        assert "File \"" not in text
