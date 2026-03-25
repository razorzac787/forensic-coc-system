import sqlite3
import os

DB_NAME = "forensics_coc.db"

def initialize_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        lead_investigator TEXT NOT NULL,
        status TEXT DEFAULT 'Open',
        created_at TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        item_type TEXT NOT NULL,
        description TEXT NOT NULL,
        collection_location TEXT NOT NULL,
        collected_by TEXT NOT NULL,
        collected_at TEXT NOT NULL,
        digital_hash TEXT,
        current_storage TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chain_of_custody (
        transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id TEXT NOT NULL,
        transferred_by TEXT NOT NULL,
        received_by TEXT NOT NULL,
        reason TEXT NOT NULL,
        transfer_time TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL,
        FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("forensic_coc Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()