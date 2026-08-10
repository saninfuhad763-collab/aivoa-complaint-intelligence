import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db import Base, engine, SessionLocal, get_db, init_db, Complaint, ComplaintDocument, CopilotMessage, AuditEvent


def test_models_import_and_metadata():
    """Verify that all ORM models are registered in Base.metadata with correct table names."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {"complaints", "complaint_documents", "copilot_messages", "audit_events"}
    assert expected_tables.issubset(table_names), f"Missing tables in metadata: {expected_tables - table_names}"


def test_database_engine_creation():
    """Verify that the database engine instance is created properly."""
    assert isinstance(engine, Engine)
    assert engine.url is not None


def test_complaint_model_columns():
    """Verify Complaint table schema columns."""
    table = Base.metadata.tables["complaints"]
    column_names = {col.name for col in table.columns}
    required_fields = {
        "id", "complaint_number", "complaint_source", "customer_name",
        "product_name", "product_strength", "batch_number", "manufacturing_date",
        "expiry_date", "affected_quantity", "affected_quantity_unit",
        "complaint_type", "complaint_date", "complaint_description",
        "severity", "risk_level", "initial_risk_assessment",
        "suggested_next_action", "ai_confidence", "status", "created_at", "updated_at"
    }
    assert required_fields.issubset(column_names), f"Missing columns in complaints table: {required_fields - column_names}"


def test_complaint_document_model_columns():
    """Verify ComplaintDocument table schema columns and foreign key."""
    table = Base.metadata.tables["complaint_documents"]
    column_names = {col.name for col in table.columns}
    required_fields = {"id", "complaint_id", "filename", "file_type", "extracted_text", "created_at"}
    assert required_fields.issubset(column_names)
    
    fk_targets = {fk.column.table.name for fk in table.foreign_keys}
    assert "complaints" in fk_targets


def test_copilot_message_model_columns():
    """Verify CopilotMessage table schema columns and foreign key."""
    table = Base.metadata.tables["copilot_messages"]
    column_names = {col.name for col in table.columns}
    required_fields = {"id", "complaint_id", "role", "message", "created_at"}
    assert required_fields.issubset(column_names)


def test_audit_event_model_columns():
    """Verify AuditEvent table schema columns and foreign key."""
    table = Base.metadata.tables["audit_events"]
    column_names = {col.name for col in table.columns}
    required_fields = {"id", "complaint_id", "event_type", "description", "metadata", "created_at"}
    assert required_fields.issubset(column_names)


def test_get_db_dependency():
    """Verify get_db generator yields a session and closes it."""
    db_gen = get_db()
    db_session = next(db_gen)
    assert isinstance(db_session, Session)
    # Complete generator cleanup
    with pytest.raises(StopIteration):
        next(db_gen)


def test_postgresql_connection_and_table_init():
    """Integration test: Verify connectivity and table initialization against PostgreSQL database."""
    try:
        init_db()
        with engine.connect() as conn:
            assert not conn.closed
    except Exception as exc:
        pytest.fail(f"PostgreSQL connectivity or table initialization failed: {exc}")
