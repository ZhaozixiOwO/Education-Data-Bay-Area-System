from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.models.base import Base


class Course(Base):
  __tablename__ = 'course'
  __table_args__ = {'extend_existing': True}
  courseId = Column(Integer, primary_key=True, autoincrement=True)
  title = Column(String(255), nullable=False)
  description = Column(Text)
  convenerId = Column(Integer, ForeignKey('oconvener.convenerId'), nullable=False)
  instructor = Column(String(255), nullable=True)
  credits = Column(Integer, nullable=True)
  
  def __init__(self, title, description, convenerId, instructor=None, credits=None):
    super(Course, self).__init__()
    self.title = title
    self.description = description
    self.convenerId = convenerId
    self.instructor = instructor
    self.credits = credits
