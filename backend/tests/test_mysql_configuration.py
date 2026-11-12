from sqlalchemy.dialects import mysql

from app.core.config import get_settings
from app.database import engine
from app.models import Base


def test_default_database_configuration_uses_mysql_pymysql() -> None:
    settings = get_settings()

    assert settings.database_url.startswith("mysql+pymysql://")
    assert engine.url.get_backend_name() == "mysql"
    assert engine.url.get_driver_name() == "pymysql"


def test_schema_compiles_for_mysql() -> None:
    dialect = mysql.dialect()

    for table in Base.metadata.sorted_tables:
        table.compile(dialect=dialect)
