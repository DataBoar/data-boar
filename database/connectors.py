"""Legacy: prefer config.loader + core.engine + connectors.sql_connector for new code."""

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from typing import Dict, Any


def get_db_connection(config: Dict[str, Any]) -> Any:
    """Cria conexão com banco de dados usando SQLAlchemy."""
    engine = create_engine(
        URL.create(
            drivername="postgresql",  # ou "mysql", "sqlite", etc.
            username=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            database=config["database"],
        )
    )
    return engine
