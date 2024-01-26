from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):
    # Table structure for Task
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    completion_criteria = Column(String)
    outcome = Column(String)
    status = Column(Text)
    start_timestamp = Column(DateTime)
    end_timestamp = Column(DateTime)


    def __str__(self):
        """
        This method returns a summary of the task in string form.
        :return: Summary of the task
        """
        return f'Task id: {self.id}, description: {self.description}, completion criteria: {self.completion_criteria}, outcome: {self.outcome}, status: {self.status}, start timestamp: {self.start_timestamp}, end timestamp: {self.end_timestamp}'

load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")

engine = create_engine(POSTGRES_URL)
Base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)

def add_task(self, description: str, completion_criteria: str, outcome: str) -> int:
    """
    This function adds a new task to the task table
    :param description: Description of the task
    :param completion_criteria: Completion criteria for the task
    :param outcome: The outcome for the task
    :return: The id of the new task
    """
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

def get_task(self, task_id: int) -> str:
    """
    This function retrieves a task based on its id from the task table
    :param task_id: The id of the task to retrieve
    :return: Task if found else return an error string
    """
    with session_maker() as session:
        task = session.query(Task).filter_by(id=task_id).first()
    
        if task is None:
            return 'No task found with that id.'
        else:
            return str(task)
        
def mark_task_as_completed(task_id: int) -> str:
    """
    Update the status of a task to 'completed'.

    Parameters:
    task_id (int): The ID of the task to be marked as completed.

    Returns:
    str: A message indicating the update status.
    """
    with session_maker() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task is None:
            return 'No task found with that id.'
        else:
            task.status = 'completed'
            session.commit()
            return 'Task marked as completed.'
        
def mark_task_as_in_progress(task_id: int) -> str:
    """
    Update the status of a task to 'in_progress'.

    Parameters:
    task_id (int): The ID of the task to be marked as in_progress.

    Returns:
    str: A message indicating the update status.
    """
    with session_maker() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task is None:
            return 'No task found with that id.'
        else:
            task.status = 'in_progress'
            session.commit()
            return 'Task marked as in_progress.'
    
    
    
def mark_task_as_failed(task_id: int) -> str:
    """
    Update the status of a task to 'failed'.

    Parameters:
    task_id (int): The ID of the task to be marked as failed.

    Returns:
    str: A message indicating the update status.
    """
    with session_maker() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task is None:
            return 'No task found with that id.'
        else:
            task.status = 'failed'
            session.commit()
            return 'Task marked as failed.'
    

def update_task(self, task_id, description, completion_criteria, outcome, status, end_timestamp) -> str:
    """
    This function updates a specific task's fields based on its id
    :param task_id: The id of the task to update
    :param description: New Description of the task
    :param completion_criteria: New Completion criteria for the task
    :param outcome: New Outcome for the task
    :param status: New Status for the task
    :param end_timestamp: New End timestamp for the task
    :return: Success string if the task is updated else returns an error string
    """
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
    
def get_available_tasks():
    with session_maker() as session:
    
        today = datetime.date.today()
        available_tasks = session.query(Task).filter(or_(Task.status == 'in progress', Task.start_date <= today)).all()
        return available_tasks