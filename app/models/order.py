from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base



class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True)
    weight = Column(String, nullable=False)
    regions = Column(Integer, nullable=False)
    delivery_hours = Column(String, nullable=False)
    costs = Column(Integer, nullable=False)
    completed_time = Column(String, nullable=True)
    courier_id = Column(Integer, nullable=True)