from sqlalchemy import Column, String, Numeric, DateTime, Integer
from app.models.base import Base
from datetime import datetime


class Pay(Base):
  __tablename__ = 'pay'
  __table_args__ = {'extend_existing': True}
  paymentId = Column(Integer, primary_key=True, autoincrement=True)
  amount = Column(Numeric(precision=15, scale=2), nullable=False)
  receiver = Column(String(50), nullable=False)
  sender = Column(String(50), nullable=False)
  paymentTime = Column(DateTime, nullable=False, default=datetime.utcnow)
  
  def __init__(self, amount, receiver, sender, paymentTime=None):
    self.amount = amount
    self.receiver = receiver
    self.sender = sender
    self.paymentTime = paymentTime if paymentTime else datetime.utcnow()
