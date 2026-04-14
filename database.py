from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st

# 1. Get the URL from Streamlit Secrets (for Cloud) or fallback to SQLite (for Local)
# In your secrets.toml it should be under [connections.postgresql]
DB_URL = st.secrets.get("DB_URL", "sqlite:///./fleet.db")

# 2. Fix for Heroku/Render/Neon (Postgres URLs often start with postgres:// but SQLAlchemy needs postgresql://)
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DB_URL, 
    pool_pre_ping=True,  # This checks if the connection is alive before using it
    pool_recycle=300,    # This refreshes the connection every 5 minutes
    connect_args={'sslmode': 'require'} # Explicitly tells Postgres to use SSL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Driver(Base):
    __tablename__ = 'drivers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    license_number = Column(String)
    vehicles = relationship("Vehicle", back_populates="driver")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    plate = Column(String)
    location = Column(String)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    driver = relationship("Driver", back_populates="vehicles")

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))
    amount = Column(Float)
    category = Column(String)
    description = Column(String)
    date = Column(String)
    receipt_path = Column(String)

class Income(Base):
    __tablename__ = 'incomes'
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))
    amount = Column(Float)
    date = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)
