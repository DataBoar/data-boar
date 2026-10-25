"""Legacy: prefer core.database.LocalDBManager and models for new code."""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

Base = declarative_base()


class BaseAuditModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DataAuditRecord(Base):
    __tablename__ = "data_audit_records"

    source_type = Column(String(50), nullable=False)
    source_name = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=True)
    column_name = Column(String(100), nullable=True)
    data_type = Column(String(50), nullable=False)
    sensitivity_level = Column(String(50), nullable=False)
    data_sample = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)


class Database:
    def __init__(self, config: dict):
        self.engine = None
        self.Session = None
        self.config = config

    def initialize(self):
        """Initialize database connection"""
        self.engine = create_engine(self.config["connection_string"])
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        Base.metadata.create_all(self.engine)

    def save_results(self, results: List[dict]):
        """Save audit results to database"""
        with self.Session() as session:
            for result in results:
                record = DataAuditRecord(
                    source_type=result["source_type"],
                    source_name=result["source_name"],
                    table_name=result["table_name"],
                    column_name=result["column_name"],
                    data_type=result["data_type"],
                    sensitivity_level=result["sensitivity_level"],
                    data_sample=result["data_sample"],
                    metadata=result["metadata"],
                )
                session.add(record)
            session.commit()
