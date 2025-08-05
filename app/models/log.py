from app.models.base import Base
from sqlalchemy import Column, String, Integer


class Log(Base):
  __tablename__ = 'systemlogs'
  __table_args__ = {'extend_existing': True}
  
  logId = Column(Integer, primary_key=True, autoincrement=True)
  userEmail = Column(String(100), nullable=False)
  identity = Column(String(100), nullable=False)
  action = Column(String(100), nullable=False)
  def __init__(self, userEmail, action, identity):
    super(Log, self).__init__()
    self.userEmail = userEmail
    self.action = action
    self.identity = identity
    