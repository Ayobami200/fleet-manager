from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st

# --- STRICT POSTGRES CONNECTION ---
try:
    # We force the app to look for the secret. No fallback allowed.
    DB_URL = st.secrets["DB_URL"]
    
    # Fix the naming convention if necessary
    if DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
        
    # Create engine with "Resiliency" settings
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={'sslmode': 'require'}
    )
    
except Exception as e:
    st.error("🚨 CRITICAL ERROR: Could not connect to the Postgres Database.")
    st.info("Check your Streamlit Secrets for 'DB_URL'.")
    st.stop() # This stops the app completely so you don't lose data

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ... (Keep your Driver, Vehicle, Expense, and Income classes exactly as they are) ...

def init_db():
    # This will now only ever run on your Neon Postgres database
    Base.metadata.create_all(bind=engine)

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
