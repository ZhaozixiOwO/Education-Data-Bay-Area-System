from datetime import datetime
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy, BaseQuery
from sqlalchemy import Column, Integer, DateTime, func
from contextlib import contextmanager


class SQLAlchemy(_SQLAlchemy):
  
  @contextmanager
  def auto_commit(self):
    try:
      yield
      db.session.commit()
    except Exception as e:
      db.session.rollback()
      raise e


db: SQLAlchemy = SQLAlchemy(query_class=BaseQuery)


class Base(db.Model):
  __abstract__ = True
  

  create_time = Column(DateTime, default=func.now())

  status = Column(Integer, default=1)
  
  def __init__(self):

    self.create_time = datetime.now()
  

  def __getitem__(self, item):
    return getattr(self, item)
  

  def set_attrs(self, attrs_dict):
    for key, value in attrs_dict.items():
      if hasattr(self, key) and key != 'id':
        setattr(self, key, value)
  

  def delete(self):
    self.status = 0
