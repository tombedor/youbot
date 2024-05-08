# from uuid import UUID

# from youbot import ENGINE, GOOGLE_EMAILS


# def store_google_email(email: str, memgpt_user_id: UUID) -> str:
#     """This function stores a google email in the database.

#     Args:
#         email (str): The email to store in the database.
#         memgpt_user_id (str): The user id to store in the database.
#     """
#     with ENGINE.connect() as connection:
#         connection.execute(GOOGLE_EMAILS.insert().values(email=email, memgpt_user_id=memgpt_user_id))
#         connection.commit()
#     return f"Linked {email} to the user."


# def fetch_google_email(memgpt_user_id: UUID) -> str:
#     """This function fetches a google email from the database.

#     Args:
#         memgpt_user_id (str): The user id to fetch from the database.

#     Returns:
#         str: The email linked to the user.
#     """
#     with ENGINE.connect() as connection:
#         row = connection.execute(GOOGLE_EMAILS.select().where(GOOGLE_EMAILS.c.memgpt_user_id == memgpt_user_id)).fetchone()
#         if row is None:
#             raise ValueError("No google email linked to the user. Get email from user and call link_google_email")
#         else:
#             return row[0]
