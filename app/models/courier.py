from sqlalchemy import Column, Integer, String, ARRAY
from app.core.database import Base



class Courier(Base):
    __tablename__ = "couriers"
    courier_id = Column(Integer, primary_key=True)
    courier_type = Column(String, nullable=False)
    regions = Column(ARRAY(Integer), nullable=False)
    working_hours = Column(String, nullable=False)