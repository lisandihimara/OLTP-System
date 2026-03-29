"""
Database configuration for OLTP Sales System
"""
from sqlalchemy import create_engine

# MySQL Database Configuration
DB_USER = 'root'
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_PORT = 3306
DATABASE_NAME = 'oltp_sales_db'

# SQLAlchemy connection string
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE_NAME}"
DATABASE_URL_WITHOUT_DB = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
engine_without_db = create_engine(DATABASE_URL_WITHOUT_DB, echo=False)
