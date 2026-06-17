from .database_manager import DatabaseManager

def execute_query(query, params=(), fetch=False):
    """
    Compatibility bridge for models using procedural execute_query.
    Redirects to the DatabaseManager singleton.
    """
    db = DatabaseManager()
    return db.execute_query(query, params, fetch=fetch)