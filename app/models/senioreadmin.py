from sqlalchemy import Column, Integer, ForeignKey
from app.models.user import User

class SeniorEAdmin(User):
  __tablename__ = 'senior_eadmin'
  __table_args__ = {'extend_existing': True}
  eadminId = Column(Integer, primary_key=True, autoincrement=True)
  tadminId = Column(Integer, ForeignKey('tadmin.tadminId'), nullable=True)
  
  def __init__(self, userId, userName, email, accessLevel, authcode, tadminId):
    super(SeniorEAdmin, self).__init__(userId, userName, email, accessLevel, authcode)
    self.tadminId = tadminId