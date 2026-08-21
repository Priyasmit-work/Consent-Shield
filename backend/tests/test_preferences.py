def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_unauthenticated_preferences_rejected(client):
    resp = client.get("/api/v1/me/preferences")
    assert resp.status_code == 401


def test_get_default_preferences(client, auth_headers):
    resp = client.get("/api/v1/me/preferences", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["mode"] == "manual"
    assert data["categories"]["essential"] is True


def test_put_preferences_round_trip(client, auth_headers):
    body = {
        "mode": "balanced",
        "categories": {
            "essential": True,
            "functional": True,
            "analytics": False,
            "advertising": False,
            "social": False,
            "unknown": False,
        },
        "auto_apply": False,
        "require_confirmation_for_unknown": True,
        "allow_network_observation": True,
        "save_scan_history": True,
    }
    resp = client.put("/api/v1/me/preferences", json=body, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["mode"] == "balanced"

    resp2 = client.get("/api/v1/me/preferences", headers=auth_headers)
    assert resp2.json()["data"]["mode"] == "balanced"


def test_essential_must_be_true(client, auth_headers):
    body = {
        "mode": "manual",
        "categories": {
            "essential": False,
            "functional": False,
            "analytics": False,
            "advertising": False,
            "social": False,
            "unknown": False,
        },
    }
    resp = client.put("/api/v1/me/preferences", json=body, headers=auth_headers)
    assert resp.status_code == 422


def test_unknown_category_cannot_be_true(client, auth_headers):
    body = {
        "mode": "custom",
        "categories": {
            "essential": True,
            "functional": False,
            "analytics": False,
            "advertising": False,
            "social": False,
            "unknown": True,
        },
    }
    resp = client.put("/api/v1/me/preferences", json=body, headers=auth_headers)
    assert resp.status_code == 422


def test_manual_mode_rejects_auto_apply(client, auth_headers):
    body = {
        "mode": "manual",
        "categories": {
            "essential": True,
            "functional": False,
            "analytics": False,
            "advertising": False,
            "social": False,
            "unknown": False,
        },
        "auto_apply": True,
    }
    resp = client.put("/api/v1/me/preferences", json=body, headers=auth_headers)
    assert resp.status_code == 422
