from app.models.base import Base
from sqlalchemy import Column, String, Integer, Float, ForeignKey


class Workspace(Base):
  __tablename__ = 'workspace'
  __table_args__ = {'extend_existing': True}
  id = Column(Integer, primary_key=True, autoincrement=True)
  convenerId = Column(Integer, ForeignKey('oconvener.convenerId'), nullable=False)  # 外键，指向OConvener
  service = Column(String(255), nullable=False)
  price = Column(Float, default=0.0)
  
  def __init__(self, convenerId, service, price):
    self.convenerId = convenerId
    self.service = service
    self.price = price
