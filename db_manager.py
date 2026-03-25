import sqlite3

DB_NAME = "forensics_coc.db"

def get_db_connection():
    """Creates a connection and configures it to return dictionary-like rows."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def get_latest_hash(evidence_id):
    """
    Fetches the CurrentHash of the most recent transfer for a specific item.
    Dev 2 needs this BEFORE they can generate a new transfer hash.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT current_hash 
            FROM chain_of_custody 
            WHERE evidence_id = ? 
            ORDER BY transfer_id DESC 
            LIMIT 1
        ''', (evidence_id,))
        result = cursor.fetchone()
        
        # If this is the very first transfer, return a standard genesis string
        return result['current_hash'] if result else "GENESIS_HASH"

def insert_transfer(payload):
    """
    Inserts a newly hashed transfer payload into the database.
    The 'payload' must exactly match the Data Contract dictionary.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO chain_of_custody (
                    evidence_id, transferred_by, received_by, 
                    reason, transfer_time, previous_hash, current_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                payload['evidence_id'], payload['transferred_by'], 
                payload['received_by'], payload['reason'], 
                payload['transfer_time'], payload['previous_hash'], 
                payload['current_hash']
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return None