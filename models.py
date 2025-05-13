# models.py
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. ORM-Basis
Base = declarative_base()

# 2. Tabelle für User-Profile
class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)     # entspricht tracker.sender_id
    height = Column(Float)
    weight = Column(Float)
    age = Column(Integer)
    goal_typ = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 3. Engine & Session-Factory
engine = create_engine("sqlite:///./fitness_coach.db")
SessionLocal = sessionmaker(bind=engine)

# 4. Funktion, um die Tabellen anzulegen
def init_db():
    Base.metadata.create_all(bind=engine)

