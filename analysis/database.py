from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database connection settings
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'tixel')
DB_USER = os.getenv('DB_USER', 'tixel')
DB_PASS = os.getenv('DB_PASS', 'tixel')

# Create engine
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Create session factory
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()

# Create base class for declarative models
Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(String, primary_key=True)
    title = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    venue_name = Column(String)
    venue_city = Column(String)
    venue_address = Column(String)
    category = Column(String)
    genre = Column(String)
    is_festival = Column(Boolean)
    raw_data = Column(JSON)
    snapshot_timestamp = Column(DateTime)
    
    tickets = relationship("Ticket", back_populates="event")

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, ForeignKey('events.id'))
    price = Column(Float)
    currency = Column(String)
    ticket_type = Column(String)
    quantity = Column(Integer)
    raw_data = Column(JSON)
    snapshot_timestamp = Column(DateTime)
    
    event = relationship("Event", back_populates="tickets")
