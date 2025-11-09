"""Tests for FastAPI endpoints."""
import os
import pytest
from fastapi.testclient import TestClient
from src.app import app

# Set deterministic hash seed
os.environ['PYTHONHASHSEED'] = '0'

client = TestClient(app)


def test_recommend_success():
    """Test successful recommendation request."""
    response = client.get("/recommend?product_id=prod_1&k=5&alpha=0.6")
    assert response.status_code == 200
    data = response.json()
    
    assert "product_id" in data
    assert "product_name" in data
    assert "alpha" in data
    assert "page_size" in data
    assert "offset" in data
    assert "total_available" in data
    assert "items" in data
    assert "next_cursor" in data
    
    assert data["product_id"] == "prod_1"
    assert data["page_size"] == 5
    assert data["alpha"] == 0.6
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5
    
    # Check item structure
    if data["items"]:
        item = data["items"][0]
        assert "product_id" in item
        assert "score" in item
        assert "reason" in item
        assert 0 <= item["score"] <= 1


def test_recommend_404():
    """Test 404 for unknown product_id."""
    response = client.get("/recommend?product_id=unknown_product&k=5")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


def test_recommend_with_cursor():
    """Test pagination with cursor."""
    # First request
    response1 = client.get("/recommend?product_id=prod_1&k=5&alpha=0.6")
    assert response1.status_code == 200
    data1 = response1.json()
    
    if data1["next_cursor"]:
        # Second request with cursor
        response2 = client.get(
            f"/recommend?product_id=prod_1&k=5&alpha=0.6&cursor={data1['next_cursor']}"
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert data2["offset"] == data1["offset"] + data1["page_size"]
        # Items should be different
        if data1["items"] and data2["items"]:
            assert data1["items"][0]["product_id"] != data2["items"][0]["product_id"]


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

