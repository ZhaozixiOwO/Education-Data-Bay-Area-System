from app.models.base import Base
from sqlalchemy import Column, Integer, String, JSON



class API(Base):
  __tablename__ = 'api_config'
  __table_args__ = {'extend_existing': True}
  id = Column(Integer, primary_key=True, autoincrement=True)
  institution_id = Column(Integer, autoincrement=True)
  base_url = Column(String(255), nullable=False)
  path = Column(String(255), nullable=False)
  method = Column(String(10), nullable=False)
  input = Column(JSON)
  output = Column(JSON)
  organizationName = Column(String(255), nullable=False)
  portContent = Column(String(255), nullable=False)
  

  
  def __init__(self, institution_id, base_url, path, method,organizationName, portContent, input=None, output=None):
    super(API, self).__init__()
    self.institution_id = institution_id
    self.base_url = base_url.rstrip('/')
    self.path = path
    self.method = method.upper()
    self.input = input
    self.output = output
    self.organizationName = organizationName
    self.portContent = portContent
  
