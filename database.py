from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    license_number = Column(String, default="")
    vehicles = relationship("Vehicle", back_populates="driver")


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    plate = Column(String, default="")
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    driver = relationship("Driver", back_populates="vehicles")
    expenses = relationship("Expense", back_populates="vehicle")
    incomes = relationship("Income", back_populates="vehicle")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    amount = Column(Float)
    description = Column(String)
    category = Column(String, default="General")
    date = Column(String)
    receipt_path = Column(String, default="")
    vehicle = relationship("Vehicle", back_populates="expenses")


class Income(Base):
    __tablename__ = "incomes"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    amount = Column(Float)
    date = Column(String)
    vehicle = relationship("Vehicle", back_populates="incomes")


engine = create_engine("sqlite:///fleet.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)