import uuid
import sqlite3
import json
from contextlib import contextmanager

DB_NAME = "cicd.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


@contextmanager
def get_db():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_column_if_missing(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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

    add_column_if_missing(cursor, 'pipelines', 'repo_id', 'TEXT')
    add_column_if_missing(cursor, 'pipelines', 'branch', 'TEXT')
    add_column_if_missing(cursor, 'pipelines', 'commit_sha', 'TEXT')
    add_column_if_missing(cursor, 'pipelines', 'triggered_by', 'TEXT DEFAULT "manual"')

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

    # Repositories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registered_repos (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        repo_url TEXT UNIQUE NOT NULL,
        webhook_id TEXT,
        webhook_secret TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    add_column_if_missing(cursor, 'registered_repos', 'webhook_id', 'TEXT')
    add_column_if_missing(cursor, 'registered_repos', 'webhook_secret', 'TEXT')

    # Branches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registered_branches (
        id TEXT PRIMARY KEY,
        repo_id TEXT NOT NULL,
        branch TEXT NOT NULL,
        last_pipeline_id TEXT,
        FOREIGN KEY (repo_id) REFERENCES registered_repos(id)
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

# Repository CRUD
def create_repo(repo: dict):
    with get_db() as conn:
        conn.execute(
            '''
            INSERT INTO registered_repos
            (id, name, repo_url, webhook_id, webhook_secret)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                repo['id'],
                repo['name'],
                repo['repo_url'],
                repo.get('webhook_id'),
                repo.get('webhook_secret')
            )
        )

def create_branch(branch: dict):
    with get_db() as conn:
        conn.execute(
            '''
            INSERT INTO registered_branches
            (id, repo_id, branch, last_pipeline_id)
            VALUES (?, ?, ?, ?)
            ''',
            (
                branch['id'],
                branch['repo_id'],
                branch['branch'],
                branch.get('last_pipeline_id')
            )
        )

def list_repos():
    with get_db() as conn:
        repos = [dict(row) for row in conn.execute(
            'SELECT * FROM registered_repos ORDER BY created_at DESC'
        ).fetchall()]

        for repo in repos:
            branches = conn.execute(
            '''
            SELECT branch, commit_sha, status, triggered_by
            FROM pipelines
            WHERE repo_id = ?
            ORDER BY rowid DESC
            ''',
            (repo['id'])
        ).fetchall()
            repo["branches"] = [
            {
                "branch": branch["branch"],
                "commit_sha": branch["commit_sha"],
                "status": branch["status"],
                "triggered_by": branch["triggered_by"]
            }
            for branch in branches
        ]

        return repos
    
def get_repo(repo_id: str):
    with get_db() as conn:
        repo = conn.execute(
            'SELECT * FROM registered_repos WHERE id = ?',
            (repo_id,)
        ).fetchone()

        if not repo:
            return None

        repo_data = dict(repo)
        branches = conn.execute(
            '''
            SELECT rb.*, p.status AS last_pipeline_status,
                   p.commit_sha, p.created_at AS last_run_at,
                   p.triggered_by
            FROM registered_branches rb
            LEFT JOIN pipelines p ON rb.last_pipeline_id = p.id
            WHERE rb.repo_id = ?
            ORDER BY rb.branch
            ''',
            (repo_id,)
        ).fetchall()

        repo_data['branches'] = [dict(row) for row in branches]
        return repo_data

def get_repo_by_url(repo_url: str):
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM registered_repos WHERE repo_url = ?',
            (repo_url,)
        ).fetchone()
        return dict(row) if row else None


def delete_repo(repo_id: str):
    with get_db() as conn:
        conn.execute('DELETE FROM registered_branches WHERE repo_id = ?', (repo_id,))
        conn.execute('DELETE FROM registered_repos WHERE id = ?', (repo_id,))


def get_branch(repo_id: str, branch: str):
    with get_db() as conn:
        row = conn.execute(
            '''
            SELECT * FROM registered_branches
            WHERE repo_id = ? AND branch = ?
            ''',
            (repo_id, branch)
        ).fetchone()
        return dict(row) if row else None


def update_branch_pipeline(repo_id: str, branch: str, pipeline_id: str):
    with get_db() as conn:
        conn.execute(
            '''
            UPDATE registered_branches
            SET last_pipeline_id = ?
            WHERE repo_id = ? AND branch = ?
            ''',
            (pipeline_id, repo_id, branch)
        )
