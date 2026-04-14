from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st

# 1. Look for the secret. If not found, use local SQLite
DB_URL = st.secrets.get("DB_URL", "sqlite:///./fleet.db")

# 2. Handle the Postgres naming convention
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# 3. Create the engine safely
if "postgresql" in DB_URL:
    # We are on the Cloud (Postgres)
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={'sslmode': 'require'}
    )
else:
    # We are Local (SQLite)
    # SQLite does NOT accept 'sslmode', so we leave it out here
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DATABASE MODELS ---
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
