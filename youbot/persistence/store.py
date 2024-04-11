from typing import Tuple
from uuid import UUID
from sqlalchemy import NullPool, create_engine

from youbot import DATABASE_URL
from youbot.persistence.youbot_user import YoubotUser
from sqlalchemy.orm import sessionmaker, mapped_column, declarative_base

Base = declarative_base()


class Store:
    def __init__(self) -> None:
        self.engine = create_engine(DATABASE_URL, poolclass=NullPool)
        Base.metadata.create_all(
            self.engine,
            tables=[
                YoubotUser.__table__,
            ],
        )
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

    def get_youbot_user(self, discord_member_id: str) -> YoubotUser:
        session = self.session_maker()
        user = session.query(YoubotUser).filter(YoubotUser.discord_member_id == discord_member_id).first()
        session.close()
        assert user
        return user


if __name__ == "__main__":
    store = Store()
