import os
from typing import List

import psycopg2


def fetch_facts(archival_only = True) -> List[str]:
    # query postgres for facts
    with psycopg2.connect(os.getenv("POSTGRES_URL")) as conn:
        with conn.cursor() as cursor:
            query = "SELECT TEXT FROM memgpt_archival_memory_agent "
            if not archival_only:
                query += " UNION ALL SELECT TEXT FROM memgpt_recall_memory_agent"
            query += ";"
                
            cursor.execute(query)
            rows = cursor.fetchall()
            return [r[0] for r in rows]
