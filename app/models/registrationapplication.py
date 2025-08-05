from sqlalchemy import Column, String, Integer, LargeBinary
from app.models.base import Base

class RegistrationApplication(Base):
  __tablename__ = 'registration_application'
  __table_args__ = {'extend_existing': True}
  applicationId = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
  organizationName = Column(String(100), nullable=False)
  oconvenerEmail = Column(String(100), nullable=False)
  proofDocuments = Column(LargeBinary, nullable=False)
  regisCode = Column(String(100), nullable=True)

  def __init__(self, organizationName, oconvenerEmail, proofDocuments, regisCode):
    super(RegistrationApplication, self).__init__()
    self.organizationName = organizationName
    self.oconvenerEmail = oconvenerEmail
    self.proofDocuments = proofDocuments
    self.regisCode = regisCode

    