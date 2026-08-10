import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure DB tables exist prior to API tests."""
    init_db()


def generate_unique_number(prefix="TEST"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def test_create_complaint():
    c_num = generate_unique_number("CREATE")
    payload = {
        "complaint_number": c_num,
        "complaint_source": "email",
        "customer_name": "Dr. Sarah Jenkins",
        "product_name": "Amoxicillin 500mg",
        "product_strength": "500mg",
        "batch_number": "BATCH-10023",
        "affected_quantity": 10.0,
        "affected_quantity_unit": "boxes",
        "complaint_type": "Packaging Defect",
        "complaint_description": "Blister seal was broken upon arrival.",
        "severity": "Medium",
        "risk_level": "Minor",
        "status": "NEW"
    }
    response = client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["complaint_number"] == c_num
    assert data["customer_name"] == "Dr. Sarah Jenkins"
    assert data["id"] is not None
    assert "created_at" in data
    assert "updated_at" in data


def test_create_duplicate_complaint_number_fails():
    c_num = generate_unique_number("DUP")
    payload = {
        "complaint_number": c_num,
        "product_name": "TestProduct"
    }
    res1 = client.post("/api/complaints", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/complaints", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_get_complaint_by_id():
    c_num = generate_unique_number("GET")
    create_res = client.post("/api/complaints", json={"complaint_number": c_num, "product_name": "PainRelief"})
    complaint_id = create_res.json()["id"]

    get_res = client.get(f"/api/complaints/{complaint_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == complaint_id
    assert get_res.json()["complaint_number"] == c_num


def test_get_nonexistent_complaint_returns_404():
    response = client.get("/api/complaints/99999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_partial_update_complaint():
    c_num = generate_unique_number("PATCH")
    create_res = client.post("/api/complaints", json={
        "complaint_number": c_num,
        "customer_name": "Original Customer",
        "product_name": "Original Product",
        "severity": "Low",
        "status": "NEW"
    })
    complaint_id = create_res.json()["id"]

    # Partial update: update status and severity without supplying customer_name or product_name
    update_res = client.patch(f"/api/complaints/{complaint_id}", json={
        "status": "IN_REVIEW",
        "severity": "High"
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["status"] == "IN_REVIEW"
    assert updated_data["severity"] == "High"
    # Verify unspecified fields were NOT overwritten with None or reset
    assert updated_data["customer_name"] == "Original Customer"
    assert updated_data["product_name"] == "Original Product"


def test_patch_nonexistent_complaint_returns_404():
    response = client.patch("/api/complaints/99999999", json={"status": "CLOSED"})
    assert response.status_code == 404


def test_delete_complaint():
    c_num = generate_unique_number("DEL")
    create_res = client.post("/api/complaints", json={"complaint_number": c_num, "product_name": "ToDelete"})
    complaint_id = create_res.json()["id"]

    del_res = client.delete(f"/api/complaints/{complaint_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == complaint_id

    # Confirm deletion
    get_res = client.get(f"/api/complaints/{complaint_id}")
    assert get_res.status_code == 404


def test_delete_nonexistent_complaint_returns_404():
    response = client.delete("/api/complaints/99999999")
    assert response.status_code == 404


def test_list_complaints_and_pagination():
    prefix = generate_unique_number("PAG")
    for i in range(5):
        client.post("/api/complaints", json={
            "complaint_number": f"{prefix}-{i}",
            "product_name": f"PaginatedProduct {i}"
        })

    list_res = client.get("/api/complaints?page=1&page_size=2")
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] >= 5


def test_list_complaints_status_filtering():
    c_num_1 = generate_unique_number("STAT1")
    c_num_2 = generate_unique_number("STAT2")

    client.post("/api/complaints", json={"complaint_number": c_num_1, "status": "CLOSED"})
    client.post("/api/complaints", json={"complaint_number": c_num_2, "status": "NEW"})

    res = client.get("/api/complaints?status=CLOSED")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(item["complaint_number"] == c_num_1 for item in items)
    assert not any(item["complaint_number"] == c_num_2 for item in items)


def test_list_complaints_severity_filtering():
    c_num_1 = generate_unique_number("SEV1")
    c_num_2 = generate_unique_number("SEV2")

    client.post("/api/complaints", json={"complaint_number": c_num_1, "severity": "Critical"})
    client.post("/api/complaints", json={"complaint_number": c_num_2, "severity": "Low"})

    res = client.get("/api/complaints?severity=Critical")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(item["complaint_number"] == c_num_1 for item in items)
    assert not any(item["complaint_number"] == c_num_2 for item in items)


def test_list_complaints_product_name_filtering():
    c_num_1 = generate_unique_number("PROD1")
    c_num_2 = generate_unique_number("PROD2")

    client.post("/api/complaints", json={"complaint_number": c_num_1, "product_name": "VeloceCure Extra"})
    client.post("/api/complaints", json={"complaint_number": c_num_2, "product_name": "OtherMed Drops"})

    res = client.get("/api/complaints?product_name=VeloceCure")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(item["complaint_number"] == c_num_1 for item in items)
    assert not any(item["complaint_number"] == c_num_2 for item in items)
