from sqlalchemy import Column, String, Integer, LargeBinary
from app.models.base import Base


class Policy(Base):
  __tablename__ = 'policy'
  
  policyId = Column(Integer, primary_key=True)
  title = Column(String(255), nullable=False)
  file_data = Column(LargeBinary, nullable=False)
  
  def __init__(self, title, file_data):
    self.title = title
    self.file_data = file_data

