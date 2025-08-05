from sqlalchemy import Column, Integer, ForeignKey, JSON
from app.models.user import User

class EAdmin(User):
  __tablename__ = 'eadmin'
  __table_args__ = {'extend_existing': True}
  eadminId = Column(Integer, primary_key=True, autoincrement=True)
  tadminId = Column(Integer, ForeignKey('tadmin.tadminId'), nullable=True)
  membershipFee = Column(JSON)
  
  def __init__(self, userId, userName, email, accessLevel, authcode, tadminId):
    super(EAdmin, self).__init__(userId, userName, email, accessLevel, authcode)
    self.tadminId = tadminId