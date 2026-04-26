import uuid
import sqlite3

DB_NAME = "cicd.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Pipelines table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipelines (
        id TEXT PRIMARY KEY,
        status TEXT
    )
    """)

    # Stages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pipeline_id TEXT,
        stage_name TEXT,
        status TEXT
    )
    """)

    # Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pipeline_id TEXT,
        stage TEXT,
        level TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def create_pipeline():
    pipeline_id = str(uuid.uuid4())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO pipelines (id, status) VALUES (?, ?)",
        (pipeline_id, "running")
    )

    conn.commit()
    conn.close()

    return pipeline_id

def update_stage(pipeline_id, stage, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM stages
    WHERE pipeline_id = ? AND stage_name = ?
    """, (pipeline_id, stage))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
        UPDATE stages SET status = ?
        WHERE pipeline_id = ? AND stage_name = ?
        """, (status, pipeline_id, stage))
    else:
        cursor.execute("""
        INSERT INTO stages (pipeline_id, stage_name, status)
        VALUES (?, ?, ?)
        """, (pipeline_id, stage, status))

    conn.commit()
    conn.close()

def add_log(pipeline_id, stage, level, message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO logs (pipeline_id, stage, level, message)
    VALUES (?, ?, ?, ?)
    """, (pipeline_id, stage, level, message))

    conn.commit()
    conn.close()


def complete_pipeline(pipeline_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE pipelines SET status = ? WHERE id = ?",
        (status, pipeline_id)
    )

    conn.commit()
    conn.close()

def get_pipeline(pipeline_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM pipelines WHERE id = ?",
        (pipeline_id,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    status = row[0]

    cursor.execute(
        "SELECT stage_name, status FROM stages WHERE pipeline_id = ?",
        (pipeline_id,)
    )
    stages = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("""
    SELECT stage, level, message, timestamp
    FROM logs
    WHERE pipeline_id = ?
    ORDER BY id
    """, (pipeline_id,))

    logs = [
        {
            "stage": r[0],
            "level": r[1],
            "message": r[2],
            "timestamp": r[3]
        }
        for r in cursor.fetchall()
    ]

    conn.close()

    return {
        "status": status,
        "stages": stages,
        "logs": logs
    }