from sqlalchemy import Column, String, Integer, ForeignKey, Float
from app.models.user import User

class DataUser(User):
  __tablename__ = 'datauser'
  __table_args__ = {'extend_existing': True}
  dataUserId = Column(Integer, primary_key=True, autoincrement=True)
  convenerId = Column(Integer, ForeignKey('oconvener.convenerId'), nullable=True)
  identity = Column(String(100), nullable=False)
  quota = Column(Float, default=0.0)
  
  def __init__(self, userId, userName, email, accessLevel, authcode, convenerId, identity, quota):
    super(DataUser,self).__init__(userId, userName, email, accessLevel, authcode)
    self.convenerId = convenerId
    self.identity = identity
    self.quota = quota
