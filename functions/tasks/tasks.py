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


engine = create_engine('postgresql://user:password@localhost/dbname')
Base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)

def add_task(self, description, completion_criteria, outcome):
    with session_maker() as session:
        new_task = Task(
            description=description,
            completion_criteria=completion_criteria,
            outcome=outcome,
            status='in progress'
        )
        session.add(new_task)
        session.commit()
    return new_task.id

def get_task(self, task_id):
    with session_maker() as session:
        task = session.query(Task).filter_by(id=task_id).first()
    
        if task is None:
            return 'No task found with that id.'
        else:
            return task
    

def update_task(self, task_id, description, completion_criteria, outcome, status, end_timestamp):
    with session_maker() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task is None:
            return 'No task found with that id.'
        else:
            task.description = description
            task.completion_criteria = completion_criteria
            task.outcome = outcome
            task.status = status
            task.end_timestamp = end_timestamp
            session.commit()
            return 'Task updated successfully.'
    
def get_available_tasks(self):
    with session_maker() as session:
        tasks_in_progress = session.query(Task).filter_by(status='in progress').all()
        return tasks_in_progress