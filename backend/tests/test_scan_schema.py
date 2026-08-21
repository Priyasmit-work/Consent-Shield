import time


def _start_scan(client, auth_headers, idempotency_key="key-1", url="https://example.com/pricing"):
    return client.post(
        "/api/v1/scans",
        json={"url": url, "scan_mode": "cookie_privacy", "execution_mode": "manual"},
        headers={**auth_headers, "Idempotency-Key": idempotency_key},
    )


def _poll_until_ready(client, auth_headers, scan_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/v1/scans/{scan_id}", headers=auth_headers)
        data = resp.json()["data"]
        if data["status"] in ("ready", "failed", "partial"):
            return data
        time.sleep(0.05)
    raise AssertionError("scan did not reach a terminal state in time")


def test_scan_requires_idempotency_key(client, auth_headers):
    resp = client.post(
        "/api/v1/scans",
        json={"url": "https://example.com", "scan_mode": "cookie_privacy", "execution_mode": "manual"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_scan_rejects_unsupported_protocol(client, auth_headers):
    resp = client.post(
        "/api/v1/scans",
        json={"url": "ftp://example.com", "scan_mode": "cookie_privacy", "execution_mode": "manual"},
        headers={**auth_headers, "Idempotency-Key": "k"},
    )
    assert resp.status_code == 422


def test_scan_lifecycle_and_json_schema(client, auth_headers):
    resp = _start_scan(client, auth_headers)
    assert resp.status_code == 202
    scan_id = resp.json()["data"]["scan_id"]

    result = _poll_until_ready(client, auth_headers, scan_id)
    assert result["status"] == "ready"
    assert result["workflow_mode"] == "explored"

    findings = result["result"]["categories"]
    assert len(findings) >= 3
    for finding in findings:
        assert finding["classification"] in ("detected", "not_detected", "unknown")
        if finding["classification"] == "detected":
            assert len(finding["evidence"]) >= 1
            for ev in finding["evidence"]:
                assert ev["source_url"]
                assert 0.0 <= ev["confidence"] <= 1.0

    plan = result["result"]["protection_plan"]
    assert "unknown" not in [c for c in plan["allowed_categories"]]


def test_duplicate_idempotency_key_reuses_scan(client, auth_headers):
    resp1 = _start_scan(client, auth_headers, idempotency_key="dup-key")
    resp2 = _start_scan(client, auth_headers, idempotency_key="dup-key")
    assert resp1.json()["data"]["scan_id"] == resp2.json()["data"]["scan_id"]


def test_second_scan_of_same_site_reuses_workflow(client, auth_headers):
    resp1 = _start_scan(client, auth_headers, idempotency_key="reuse-1", url="https://reuse-demo.com/tos")
    scan_id_1 = resp1.json()["data"]["scan_id"]
    _poll_until_ready(client, auth_headers, scan_id_1)

    resp2 = _start_scan(client, auth_headers, idempotency_key="reuse-2", url="https://reuse-demo.com/pricing")
    scan_id_2 = resp2.json()["data"]["scan_id"]
    result2 = _poll_until_ready(client, auth_headers, scan_id_2)

    assert result2["workflow_mode"] == "reused"


def test_delete_scan(client, auth_headers):
    resp = _start_scan(client, auth_headers, idempotency_key="del-1", url="https://delete-demo.com")
    scan_id = resp.json()["data"]["scan_id"]
    _poll_until_ready(client, auth_headers, scan_id)

    del_resp = client.delete(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert get_resp.status_code == 404
