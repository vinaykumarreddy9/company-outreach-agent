import psycopg2
from backend.config.settings import settings
import os

def init_db():
    print("Connecting to Neon DB...")
    try:
        conn = psycopg2.connect(settings.NEON_DB_URL)
        cur = conn.cursor()
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), "db_schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            
        print("Applying schema...")
        cur.execute(schema_sql)
        conn.commit()
        
        print("Database initialized successfully!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Improve error handling for better debugging
        if "password authentication failed" in str(e):
             print("Check your NEON_DB_URL credentials.")
        raise e

if __name__ == "__main__":
    init_db()
