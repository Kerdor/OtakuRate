from sqlalchemy import text

from otakurate.database import Base, SessionLocal, engine


def test_database_connection():
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_session_can_begin_transaction():
    with SessionLocal.begin() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1


def test_base_contains_current_domain_tables():
    assert "titles" in Base.metadata.tables
