import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def upgrade_database():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()

    # 1. Create the new enterprise tables
    queries = [
        """
        CREATE TABLE IF NOT EXISTS cases (
            case_id VARCHAR(50) PRIMARY KEY,
            lead_investigator_badge VARCHAR(50),
            status VARCHAR(50),
            created_at DATETIME,
            FOREIGN KEY (lead_investigator_badge) REFERENCES personnel(badge_number)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS evidence_cases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            case_id VARCHAR(50),
            evidence_id VARCHAR(50),
            linked_by_badge VARCHAR(50),
            notes TEXT,
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(case_id),
            FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id),
            FOREIGN KEY (linked_by_badge) REFERENCES personnel(badge_number)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS lab_requests (
            request_id INT AUTO_INCREMENT PRIMARY KEY,
            evidence_id VARCHAR(50),
            requested_by_badge VARCHAR(50),
            test_type VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Pending',
            summary TEXT,
            file_path TEXT,
            equipment VARCHAR(100),
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id),
            FOREIGN KEY (requested_by_badge) REFERENCES personnel(badge_number)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS legal_dispositions (
            disposition_id INT AUTO_INCREMENT PRIMARY KEY,
            evidence_id VARCHAR(50),
            action_type VARCHAR(100),
            authorized_by_badge VARCHAR(50),
            witnessed_by_badge VARCHAR(50),
            court_order VARCHAR(100),
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id),
            FOREIGN KEY (authorized_by_badge) REFERENCES personnel(badge_number),
            FOREIGN KEY (witnessed_by_badge) REFERENCES personnel(badge_number)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS temperature_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            location_id VARCHAR(50),
            temperature_celsius DECIMAL(5,2),
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES storage_locations(location_id)
        )
        """
    ]

    for q in queries:
        cursor.execute(q)

   
    try:
        cursor.execute("ALTER TABLE storage_locations ADD COLUMN IF NOT EXISTS storage_type VARCHAR(100);")
        cursor.execute("ALTER TABLE storage_locations ADD COLUMN IF NOT EXISTS requires_temp_monitoring BOOLEAN DEFAULT FALSE;")
    except Exception as e:
        pass

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Enterprise Database Schema Upgraded Successfully!")

if __name__ == "__main__":
    upgrade_database()
