import os
from sqlalchemy import (
    UUID,
    Column,
    Integer,
    MetaData,
    NullPool,
    String,
    ForeignKey,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
postgres_url = os.getenv("POSTGRES_URL")
engine = create_engine(postgres_url, poolclass=NullPool)
metadata = MetaData()

LISTS = Table(
    "lists",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("user_id", UUID),
    UniqueConstraint("name", "user_id"),
)

LIST_ITEMS = Table(
    "list_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("content", String),
    Column("list_id", Integer, ForeignKey("lists.id")),
    UniqueConstraint("content", "list_id"),
)

metadata.create_all(engine)


def create_list(self, list_name: str) -> str:
    """Creates a list with the given name for the user

    Args:
        list_name (str): The name of the list

    Returns:
        str: The result of the list creation attempt.
    """
    with engine.connect() as connection:
        connection.execute(
            LISTS.insert().values(name=list_name, user_id=self.agent_state.user_id)
        )
        connection.commit()
    return f"created list {list_name}"


def get_lists(self) -> str:
    """Gets the names of all lists for the user

    Returns:
        str: The result of the list retrieval attempt.
    """
    with engine.connect() as connection:
        user_id = self.agent_state.user_id
        lists = connection.execute(
            LISTS.select().where(LISTS.c.user_id == user_id)
        ).fetchall()
        lists = [list_row[1] for list_row in lists]
    return f"retrieved lists {lists}"


def add_list_item(self, list_name: str, item_content: str) -> str:
    """Adds an item to the list with the given name

    Args:
        list_name (str): The name of the list
        item_content (str): The content of the item to add

    Returns:
        str: The result of the list item addition attempt.
    """
    with engine.connect() as connection:
        user_id = self.agent_state.user_id
        list_row = connection.execute(
            LISTS.select().where(
                LISTS.c.name == list_name and LISTS.c.user_id == user_id
            )
        ).fetchone()
        if list_row is None:
            raise ValueError(f"No list with name {list_name} exists for the user")
        list_id = list_row[0]
        connection.execute(
            LIST_ITEMS.insert().values(content=item_content, list_id=list_id)
        )
        connection.commit()
    return f"added item {item_content} to list {list_name}"


def get_list_items(self, list_name: str) -> str:
    """Gets the items in the list with the given name

    Args:
        list_name (str): The name of the list

    Returns:
        str: The result of the list retrieval attempt.
    """
    with engine.connect() as connection:
        user_id = self.agent_state.user_id
        list_row = connection.execute(
            LISTS.select().where(
                LISTS.c.name == list_name and LISTS.c.user_id == user_id
            )
        ).fetchone()
        if list_row is None:
            raise ValueError(f"No list with name {list_name} exists for the user")
        list_id = list_row[0]
        list_items = connection.execute(
            LIST_ITEMS.select().where(LIST_ITEMS.c.list_id == list_id)
        ).fetchall()
        list_items = [list_item[1] for list_item in list_items]
    return f"retrieved items {list_items} from list {list_name}"


def remove_list_item(self, list_name: str, item_content: str) -> str:
    """Removes an item from the list with the given name

    Args:
        list_name (str): The name of the list
        item_content (str): The content of the item to remove

    Returns:
        str: The result of the list item removal attempt.
    """
    with engine.connect() as connection:
        connection.execute(
            LIST_ITEMS.delete().where(LIST_ITEMS.c.content == item_content)
        )
        connection.commit()
    return f"removed item {item_content} from list {list_name}"
