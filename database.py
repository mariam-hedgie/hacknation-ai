from databricks import sql
import os
from dotenv import load_dotenv
import logging


logging.getLogger("databricks.sql").setLevel(logging.WARNING)
load_dotenv()

catalog = "workspace"   
schema = "default"    
table = f"{catalog}.{schema}.facilities_searchable"

def build_query(user_request):
    specialties = user_request.get("specialties", [])
    procedures = user_request.get("procedures", [])
    
    conditions = []
    
    if specialties:
        specialty_list = "', '".join(specialties)
        conditions.append(f"arrays_overlap(specialties, {specialty_list})")
    
    if procedures:
        procedure_list = "', '".join(procedures)
        conditions.append(f"arrays_overlap(procedures, {procedure_list})")
    
    where_clause = " OR ".join(conditions) if conditions else "1=1"
    
    return f"""
    SELECT *
    FROM {table}
    WHERE {where_clause}
    LIMIT 10
    """

def query_db(query, params=None):
    connection = sql.connect(
        server_hostname=os.getenv("SERVER_HOSTNAME"),
        http_path=os.getenv("HTTP_PATH"),
        access_token=os.getenv("ACCESS_TOKEN")
    )

    try:
        cursor = connection.cursor()

        cursor.execute(query, params or {})
        results = cursor.fetchall()

        cursor.close()

        return results

    finally:
        cursor.close()
        connection.close()
