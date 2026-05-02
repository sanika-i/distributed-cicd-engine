import uuid
import sqlite3
import json
import os

DB_NAME = os.path.join(os.getenv("DB_DIR", "."), "cicd.db")

def get_connection():
    db_dir = os.getenv("DB_DIR", ".")
    os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Pipelines table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipelines (
    id TEXT PRIMARY KEY,
    status TEXT,
    repo_name TEXT,
    branch_name TEXT,
    commit_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

    # Pipeline State
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_state (
        pipeline_id     TEXT PRIMARY KEY,
        repo_url        TEXT,
        branch          TEXT,
        commit_sha      TEXT,
        remaining_stages TEXT,
        pipeline_def    TEXT
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

    cursor.execute(
        "DELETE FROM pipeline_state WHERE pipeline_id = ?",
        (pipeline_id,)
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

def list_pipelines():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM pipelines ORDER BY rowid DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"pipeline_id": r[0], "status": r[1]} for r in rows]

def save_pipeline_state(pipeline_id, repo_url, branch, commit_sha, remaining_stages, pipeline_def):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO pipeline_state
        (pipeline_id, repo_url, branch, commit_sha, remaining_stages, pipeline_def)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        pipeline_id,
        repo_url,
        branch,
        commit_sha,
        json.dumps(remaining_stages),
        json.dumps(pipeline_def)
    ))
    conn.commit()
    conn.close()

def get_pipeline_state(pipeline_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT repo_url, branch, commit_sha, remaining_stages, pipeline_def
    FROM pipeline_state WHERE pipeline_id = ?
    """, (pipeline_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "repo_url":         row[0],
        "branch":           row[1],
        "commit_sha":       row[2],
        "remaining_stages": json.loads(row[3]),
        "pipeline_def":     json.loads(row[4])
    }

def update_pipeline_state(pipeline_id, remaining_stages):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pipeline_state SET remaining_stages = ? WHERE pipeline_id = ?",
        (json.dumps(remaining_stages), pipeline_id)
    )
    conn.commit()
    conn.close()

def recover_interrupted_pipelines():
    """
    On startup, any pipeline still marked 'running' was interrupted
    by a previous shutdown. Mark them failed so they don't sit stuck forever.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pipelines SET status = 'failed'
        WHERE status = 'running'
    """)
    cursor.execute("""
        DELETE FROM pipeline_state
        WHERE pipeline_id IN (
            SELECT id FROM pipelines WHERE status = 'failed'
        )
    """)
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected:
        print(f"[startup] Marked {affected} interrupted pipeline(s) as failed")
