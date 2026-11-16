"""API endpoint tests."""
import pytest

@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VeriShop"

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

@pytest.mark.asyncio
async def test_search_endpoint(async_client):
    response = await async_client.post("/api/v1/search", json={"query": "wireless headphones", "max_results": 3})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "request_id" in data
    assert data["total_found"] > 0

@pytest.mark.asyncio
async def test_search_missing_query(async_client):
    response = await async_client.post("/api/v1/search", json={})
    assert response.status_code == 422  # Validation error
