from app.models.base import Base
from sqlalchemy import Column, String, Integer


class User(Base):
  __abstract__ = True
  userId = Column(Integer, autoincrement=True)
  userName = Column(String(100), nullable=False)
  email = Column(String(100), nullable=False)
  accessLevel = Column(String(100), nullable=False)
  authcode = Column(String(100), nullable=True, default=None)
  
  def __init__(self, userId, userName, email, accessLevel, authcode):
    super(User, self).__init__()
    self.userId = userId
    self.userName = userName
    self.email = email
    self.accessLevel = accessLevel
    self.authcode = authcode
  
  def getUserId(self):
    return self.userId
  
  def getUserName(self):
    return self.userName
  
  def getEmail(self):
    return self.email
  
  def setUserName(self, userName):
    self.userName = userName
    
    
    