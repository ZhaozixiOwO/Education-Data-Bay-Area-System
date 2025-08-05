from sqlalchemy import Column, Integer
from app.models.user import User


class TAdmin(User):
  __tablename__ = 'tadmin'
  __table_args__ = {'extend_existing': True}
  tadminId = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
  
  def __init__(self, userId, userName, email, accessLevel, authcode, tadminId):
    super(TAdmin, self).__init__(userId, userName, email, accessLevel, authcode)
    self.tadminId = tadminId
  