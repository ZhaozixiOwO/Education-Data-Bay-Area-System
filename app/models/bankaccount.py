from sqlalchemy import Column, Integer, String
from app.models.base import Base


class BankAccount(Base):
  __tablename__ = 'bank_account'
  __table_args__ = {'extend_existing': True}
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String(50), nullable=False, unique=True)
  account = Column(String(50), nullable=False)
  bank = Column(String(50), nullable=False)
  __password = Column("password", String(50), nullable=False)
  organizationName = Column(String(100), nullable=False)
  
  def __init__(self, name, account, bank, password, organizationName):
    super(BankAccount, self).__init__()
    self.name = name
    self.account = account
    self.bank = bank
    self.__password = password
    self.organizationName = organizationName
  
  def get_password(self):
    return self.__password
  
  def set_password(self, password):
    self.__password = password
  
  def to_dict(self):
    return {
      "account_name": self.name,
      "account_number": self.account,
      "bank": self.bank,
      "password": self.get_password()
    }
