"""Unit tests for FastAPI endpoints."""

import io
import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["engine"] == "Content Intelligence Engine"
    assert "version" in data


def test_analyze_endpoint_with_json_text():
    payload = {
        "text": "SEBI registered advisor Rahul Sharma. Guaranteed 40% returns. Pay ₹5,000.",
        "channel": "telegram"
    }
    response = client.post("/api/v1/content/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] is not None
    assert data["source"]["type"] == "text"
    assert data["source"]["channel"] == "telegram"
    assert data["content_features"]["contains_financial_content"] is True
    assert any(p["normalized"] == "Rahul Sharma" for p in data["entities"]["people"])
    assert any(r["text"] == "SEBI" for r in data["entities"]["regulators"])
    assert any(a["value"] == 5000.0 for a in data["structured_signals"]["currency_amounts"])


def test_analyze_endpoint_with_image_upload():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (300, 100), color="white")
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Guaranteed returns", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test.png", buf, "image/png")}
    data = {"channel": "whatsapp"}
    response = client.post("/api/v1/content/analyze", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["provenance"]["ocr_used"] is True
    assert res_data["source"]["type"] == "image"
    assert res_data["source"]["channel"] == "whatsapp"


def test_analyze_endpoint_empty_content_warning():
    payload = {
        "text": "",
        "channel": "unknown"
    }
    response = client.post("/api/v1/content/analyze", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] in {"partial", "failed"}
    assert any("No readable text" in w for w in res_data["warnings"])
