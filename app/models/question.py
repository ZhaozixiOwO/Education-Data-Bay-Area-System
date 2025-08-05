from sqlalchemy import Column, Integer, String, Text
from app.models.base import Base


class Question(Base):
  __tablename__ = 'question'
  __table_args__ = {'extend_existing': True}
  questionId = Column(Integer, primary_key=True, autoincrement=True)
  question = Column(Text, nullable=False)
  userEmail = Column(String(50), nullable=False)
  answer = Column(Text)
  
  def __init__(self, question, userEmail, answer):
    super(Question, self).__init__()
    self.question = question
    self.userEmail = userEmail
    self.answer = answer