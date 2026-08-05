from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_read_candles_default():
    response = client.get("/api/v1/candles?resolution=1m&mode=price&limit=10")
    assert response.status_code == 200
    data = response.json()

    # Assert payload structure invariants
    assert "candles" in data
    assert "markers" in data
    assert isinstance(data["candles"], list)

    # If data is present, verify candle schema
    if len(data["candles"]) > 0:
        candle = data["candles"][0]
        assert "time" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle

def test_read_candles_default():
    response = client.get("/api/v1/candles?resolution=1m&mode=price&limit=10")
    print(f"\nDEBUG RAW RESPONSE TEXT: {response.text}")
    print(f"DEBUG RESPONSE STATUS: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert "candles" in data