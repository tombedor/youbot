import logging
from memgpt import MemGPT
from datetime import datetime
from memgpt.metadata import MetadataStore, AgentModel
from memgpt.agent_store.db import get_db_model
from memgpt.agent_store.storage import TableType, RECALL_TABLE_NAME, ARCHIVAL_TABLE_NAME

client = MemGPT()


def create_agent_checkpoint(self) -> str:
    """Creates a backup of the current agent state

    Returns:
        str: the result of the backup operation
    """

    with MetadataStore().session_maker() as session:
        row = (
            session.query(AgentModel)
            .filter(AgentModel.id == self.agent_state.id)
            .first()
        )
        
        assert(row)

        # new name, _bkp_YYYYMMDDHHMMSS
        new_name = f"{row.name}_bkp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_row = AgentModel()

        for key, value in row.__dict__.items():
            if (
                key != "id" and key != "_sa_instance_state"
            ):  # Exclude these special fields
                setattr(new_row, key, value)
                new_row.name = new_name # type: ignore
        session.add(new_row)
        session.commit()
    return f"Created state backup with name {new_name}"


def copy_memories(self, source_agent_id: str, dest_agent_id: str) -> str:
    """Copies memories between agents

    Args:
        source_agent_id (str): id of agent with memries
        dest_agent_id (str): id of agent to recieve memories

    Returns:
        str: the result of the copy operation
    """
    msgs = []
    get_db_model(RECALL_TABLE_NAME, TableType.RECALL_MEMORY, user_id=client.user_id)
    for table_type, table_name in (
        (TableType.RECALL_MEMORY, RECALL_TABLE_NAME),
        (TableType.ARCHIVAL_MEMORY, ARCHIVAL_TABLE_NAME),
    ):
        logging.info(f"Copying {table_name} from {source_agent_id} to {dest_agent_id}")
        db_model = get_db_model(
            table_name=table_name, table_type=table_type, user_id=client.user_id
        )

        with MetadataStore.session_maker() as session: # type: ignore
            existing_rows = (
                session.query(db_model).filter(db_model.agent_id == dest_agent_id).all()
            )
            distinct_text_values = set(row.text for row in existing_rows)
            rows = (
                session.query(db_model)
                .filter(db_model.agent_id == source_agent_id)
                .all()
            )

            rows_to_insert = []

            for row in rows:
                # filter out system messages
                if (
                    '"status": "OK", "message": "None"' in row.text
                    or row.text in distinct_text_values
                ):
                    continue

                row.agent_id = dest_agent_id
                rows_to_insert.append(row)
                distinct_text_values.add(row.text)

            for row in rows_to_insert:
                new_row = db_model()
                for key, value in row.__dict__.items():
                    if (
                        key != "id" and key != "_sa_instance_state"
                    ):  # Exclude these special fields
                        setattr(new_row, key, value)
                        new_row.agent_id = dest_agent_id
                        session.add(new_row)
                session.add(row)
            msgs.append(f"adding {len(rows_to_insert)} rows into table {table_name}")
        session.commit()
    return "\n".join(msgs)
