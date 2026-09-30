import sqlite3
import datetime

class PHCEdgeNode:
    """
    Runs at the local Primary Health Centre (PHC).
    Stores inventory locally and formats SMS fallback payloads when internet fails.
    """
    def __init__(self, phc_id="PHC-LKO-101", db_name="phc_local.db"):
        self.phc_id = phc_id
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS local_inventory (
                    medicine_code TEXT PRIMARY KEY,
                    medicine_name TEXT,
                    stock INTEGER,
                    min_threshold INTEGER,
                    expiry_date TEXT,
                    last_updated TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_telemetry (
                    date TEXT PRIMARY KEY,
                    footfall INTEGER,
                    bed_occupancy INTEGER,
                    doctors_present INTEGER
                )
            """)
            conn.commit()

    def update_stock(self, code, name, stock, min_threshold, expiry_date):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO local_inventory 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, name, stock, min_threshold, expiry_date, datetime.datetime.now()))
            conn.commit()

    def generate_sms_fallback_payload(self, footfall, beds, docs):
        """
        Compresses local telemetry into a compact SMS payload (< 140 chars)
        Format: PHC_ID|MED1:QTY,MED2:QTY|BED:X|DOC:Y|FT:Z
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT medicine_code, stock FROM local_inventory")
            items = cursor.fetchall()
            
        med_str = ",".join([f"{code}:{stock}" for code, stock in items])
        sms_payload = f"{self.phc_id}|{med_str}|BED:{beds}|DOC:{docs}|FT:{footfall}"
        return sms_payload

if __name__ == "__main__":
    node = PHCEdgeNode()
    node.update_stock("PAR", "Paracetamol Syrup", 120, 100, "2026-12-31")
    node.update_stock("AMX", "Amoxicillin 500mg", 15, 50, "2026-10-15")
    node.update_stock("INS", "Insulin Regular", 12, 30, "2026-11-20")
    
    payload = node.generate_sms_fallback_payload(footfall=85, beds=18, docs=2)
    print("Edge Database Synchronized.")
    print("Generated Zero-Connectivity SMS Payload:")
    print(payload)