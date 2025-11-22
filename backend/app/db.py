from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'admin.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def ensure_schema():
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(patients)")
        cols = {row[1] for row in cur.fetchall()}
        if 'external_id' not in cols:
            cur.execute("ALTER TABLE patients ADD COLUMN external_id TEXT")
        if 'visit_time' not in cols:
            cur.execute("ALTER TABLE patients ADD COLUMN visit_time DATETIME")
        if 'medical_record_no' not in cols:
            cur.execute("ALTER TABLE patients ADD COLUMN medical_record_no TEXT")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_mrn ON patients(medical_record_no)")
        conn.commit()
    finally:
        conn.close()