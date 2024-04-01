
from sqlalchemy import NullPool, create_engine

from youbot import POSTGRES_URL
from youbot.persistence.youbot_user import YoubotUser
from sqlalchemy.orm import sessionmaker, mapped_column, declarative_base

Base = declarative_base()

class Store:
    def __init__(self) -> None:
        self.engine = create_engine(POSTGRES_URL, poolclass=NullPool)
        Base.metadata.create_all(self.engine, tables=[YoubotUser.__table__,])
        self.session_maker = sessionmaker(bind=self.engine)
        
    def create_user(self, user: YoubotUser) -> None:
        with self.session_maker() as session:
            session.add(user)
            session.commit()
        
    def get_user_by_email(self, email: str) -> YoubotUser:
        session = self.session_maker()
        user = session.query(YoubotUser).filter(YoubotUser.email == email).first()
        session.close()
        return user

if __name__ == "__main__":
    store = Store()
    
        
    