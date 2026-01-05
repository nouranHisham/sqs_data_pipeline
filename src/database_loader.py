import psycopg2
import json
import time
from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)

def wait_for_postgres(host, port, user, password, db, retries=10, delay=3):
    for i in range(retries):
        try:
            conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=db)
            print("Postgres is ready!")
            return conn
        except psycopg2.OperationalError:
            print(f"Postgres not ready yet ({i+1}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    raise Exception("Postgres not available after retries")

def create_database():
    conn = wait_for_postgres(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        db="postgres"
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s;",
            (DB_NAME,)
        )
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"Database '{DB_NAME}' created.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

    conn.close()

def get_db_connection():
    return wait_for_postgres(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME
    )

def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                mail TEXT NOT NULL,
                name TEXT NOT NULL,
                trip JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP
            )
        """)
        conn.commit()


def insert_event(conn, event):
    with conn.cursor() as cur:
        # Convert trip to JSON string
        trip_json = json.dumps(event["trip"])
        
        # Upsert query: insert new or update if changed
        cur.execute("""
            INSERT INTO events (id, mail, name, trip)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET
                mail = EXCLUDED.mail,
                name = EXCLUDED.name,
                trip = EXCLUDED.trip,
                updated_at = NOW()
            WHERE
                events.mail IS DISTINCT FROM EXCLUDED.mail OR
                events.name IS DISTINCT FROM EXCLUDED.name OR
                events.trip IS DISTINCT FROM EXCLUDED.trip
        """, (
            event["id"],
            event["mail"],
            event["name"],
            trip_json
        ))
        conn.commit()
