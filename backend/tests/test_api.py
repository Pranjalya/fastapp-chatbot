import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "default_provider" in data

@pytest.mark.asyncio
async def test_login_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Valid login
        res = await client.post("/api/auth/login", json={"username": "kvothe", "password": "password123"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["username"] == "kvothe"

        # Invalid login
        res_fail = await client.post("/api/auth/login", json={"username": "kvothe", "password": "wrongpassword"})
        assert res_fail.status_code == 401

@pytest.mark.asyncio
async def test_models_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        provider_ids = [p["id"] for p in data["providers"]]
        assert "gemini" in provider_ids
        assert "nvidia" in provider_ids
        assert "openai" in provider_ids
