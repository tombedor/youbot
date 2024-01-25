from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):
   __tablename__ = 'tasks'

   id = Column(Integer, primary_key=True)
   description = Column(String)
   completion_criteria = Column(String)
   outcome = Column(String)
   status = Column(Text)
   start_timestamp = Column(DateTime)
   end_timestamp = Column(DateTime)

def setup_database():
   engine = create_engine('postgresql://user:password@localhost/dbname')
   Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def add_task(description, completion_criteria, outcome):
    session = Session()
    new_task = Task(
        description=description,
        completion_criteria=completion_criteria,
        outcome=outcome,
        status='in progress'
    )
    session.add(new_task)
    session.commit()
    return new_task.id

def get_task(task_id):
    session = Session()
    task = session.query(Task).filter_by(id=task_id).first()
    session.close()
    if task is None:
        return 'No task found with that id.'
    else:
        return task
    

def update_task(task_id, description, completion_criteria, outcome, status, end_timestamp):
    session = Session()
    task = session.query(Task).filter_by(id=task_id).first()
    if task is None:
        session.close()
        return 'No task found with that id.'
    else:
        task.description = description
        task.completion_criteria = completion_criteria
        task.outcome = outcome
        task.status = status
        task.end_timestamp = end_timestamp
        session.commit()
        session.close()
        return 'Task updated successfully.'    