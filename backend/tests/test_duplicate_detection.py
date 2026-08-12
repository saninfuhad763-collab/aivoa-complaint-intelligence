"""
Unit & Integration Tests for Duplicate Complaint Detection API

Tests coverage:
1. No duplicate found
2. Exact product_name + batch_number duplicate (High confidence)
3. Case and whitespace normalization
4. Same product_name + customer_name duplicate (Medium confidence)
5. Different batch with same customer (Medium confidence)
6. Self-exclusion (exclude_id parameter)
7. Missing product_name
8. Missing batch_number
9. Candidate limit capping (max 5 candidates)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure DB tables exist prior to duplicate tests."""
    init_db()


def generate_unique_number(prefix="DUPTEST"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def create_sample_complaint(product_name: str, batch_number: str, customer_name: str = "John Doe") -> dict:
    c_num = generate_unique_number()
    payload = {
        "complaint_number": c_num,
        "product_name": product_name,
        "batch_number": batch_number,
        "customer_name": customer_name,
        "complaint_type": "Quality Defect",
        "complaint_description": "Sample complaint text for testing",
        "status": "NEW"
    }
    res = client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    return res.json()


def test_no_duplicate():
    """TEST 1 — Unique product and batch returns no duplicates."""
    create_sample_complaint("Amoxicillin 250mg", "AMX-2026-001")

    res = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Paracetamol 500mg",
        "batch_number": "PCM-2026-999"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["has_duplicates"] is False
    assert data["duplicates"] == []


def test_exact_product_and_batch_duplicate():
    """TEST 2 — Matching product and batch returns high confidence duplicate."""
    created = create_sample_complaint("Paracetamol 500mg", "PCM-2026-001")

    res = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Paracetamol 500mg",
        "batch_number": "PCM-2026-001"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["has_duplicates"] is True
    assert len(data["duplicates"]) >= 1
    high_matches = [d for d in data["duplicates"] if d["id"] == created["id"]]
    assert len(high_matches) == 1
    dup = high_matches[0]
    assert dup["match_confidence"] == "high"
    assert dup["match_reason"] == "Same product name and batch/lot number."


def test_case_and_whitespace_normalization():
    """TEST 3 — Case differences and surrounding spaces match correctly."""
    created = create_sample_complaint("Ibuprofen 400mg", "IBU-2026-005")

    res = client.post("/api/complaints/check-duplicates", json={
        "product_name": "  ibuprofen 400MG  ",
        "batch_number": " ibu-2026-005 "
    })
    assert res.status_code == 200
    data = res.json()
    assert data["has_duplicates"] is True
    matching = [d for d in data["duplicates"] if d["id"] == created["id"]]
    assert len(matching) == 1
    assert matching[0]["match_confidence"] == "high"


def test_same_product_same_customer_medium_confidence():
    """TEST 4 & 5 — Same product and customer but different batch returns medium confidence."""
    created = create_sample_complaint("Metformin 500mg", "MET-2026-001", "Alice Smith")

    res = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Metformin 500mg",
        "batch_number": "MET-2026-002",
        "customer_name": "Alice Smith"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["has_duplicates"] is True
    matching = [d for d in data["duplicates"] if d["id"] == created["id"]]
    assert len(matching) == 1
    dup = matching[0]
    assert dup["match_confidence"] == "medium"
    assert dup["match_reason"] == "Same product name reported by the same customer."


def test_self_exclusion():
    """TEST 6 — Passing exclude_id prevents returning the complaint itself as a duplicate."""
    created = create_sample_complaint("Aspirin 100mg", "ASP-2026-010")

    # Without exclude_id -> returns duplicate
    res1 = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Aspirin 100mg",
        "batch_number": "ASP-2026-010"
    })
    matching1 = [d for d in res1.json()["duplicates"] if d["id"] == created["id"]]
    assert len(matching1) == 1

    # With exclude_id = created['id'] -> complaint is excluded
    res2 = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Aspirin 100mg",
        "batch_number": "ASP-2026-010",
        "exclude_id": created["id"]
    })
    assert res2.status_code == 200
    matching2 = [d for d in res2.json()["duplicates"] if d["id"] == created["id"]]
    assert len(matching2) == 0


def test_missing_product_name():
    """TEST 7 — Empty or null product_name returns no duplicates."""
    create_sample_complaint("Omeprazole 20mg", "OMP-2026-001")

    res = client.post("/api/complaints/check-duplicates", json={
        "product_name": "",
        "batch_number": "OMP-2026-001"
    })
    assert res.status_code == 200
    assert res.json()["has_duplicates"] is False


def test_missing_batch_number():
    """TEST 8 — Empty batch number skips high confidence rule."""
    customer_name = f"Bob_{uuid.uuid4().hex[:4]}"
    created = create_sample_complaint("Loratadine 10mg", "LOR-2026-001", customer_name)

    # Without customer name and without batch number -> no match
    res1 = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Loratadine 10mg",
        "batch_number": ""
    })
    matching1 = [d for d in res1.json()["duplicates"] if d["id"] == created["id"]]
    assert len(matching1) == 0

    # With customer name -> medium match
    res2 = client.post("/api/complaints/check-duplicates", json={
        "product_name": "Loratadine 10mg",
        "customer_name": customer_name
    })
    matching2 = [d for d in res2.json()["duplicates"] if d["id"] == created["id"]]
    assert len(matching2) == 1
    assert matching2[0]["match_confidence"] == "medium"


def test_maximum_candidates_limit():
    """TEST 9 — Limits returned duplicate candidates to maximum 5."""
    prod = f"Atorvastatin_{uuid.uuid4().hex[:4]}"
    for _ in range(7):
        create_sample_complaint(prod, "ATO-2026-999")

    res = client.post("/api/complaints/check-duplicates", json={
        "product_name": prod,
        "batch_number": "ATO-2026-999"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["has_duplicates"] is True
    assert len(data["duplicates"]) == 5
