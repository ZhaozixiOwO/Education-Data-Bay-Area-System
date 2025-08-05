from sqlalchemy import Column, String, Integer
from app.models.user import User

class OConvener(User):
  __tablename__ = 'oconvener'
  __table_args__ = {'extend_existing': True}
  convenerId = Column(Integer, primary_key=True,nullable=False)
  organizationName = Column(String(100), nullable=False)

  
  def __init__(self, userId, userName, email, accessLevel, authcode, organizationName):
    super(OConvener, self).__init__(userId, userName, email, accessLevel, authcode)
    self.organizationName = organizationName