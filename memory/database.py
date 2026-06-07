import sqlite3

DB_NAME = "memory/research.db"


import json

def init_db():

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            route TEXT,
            report TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Run column migrations
    cursor.execute("PRAGMA table_info(research_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "sources" not in columns:
        cursor.execute("ALTER TABLE research_history ADD COLUMN sources TEXT")
    if "insights" not in columns:
        cursor.execute("ALTER TABLE research_history ADD COLUMN insights TEXT")

    conn.commit()
    conn.close()

def save_research(
    query,
    route,
    report,
    sources=None,
    insights=None
):

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    sources_json = json.dumps(sources or [])
    insights_json = json.dumps(insights or {})

    cursor.execute(
        """
        INSERT INTO research_history
        (
            query,
            route,
            report,
            sources,
            insights
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            query,
            route,
            report,
            sources_json,
            insights_json
        )
    )

    conn.commit()
    conn.close()


def get_history():

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            query,
            route,
            timestamp
        FROM research_history
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_report_by_id(report_id):

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            query,
            route,
            report,
            timestamp,
            sources,
            insights
        FROM research_history
        WHERE id = ?
        """,
        (report_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return row

def get_latest_report():

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            query,
            route,
            report,
            timestamp
        FROM research_history
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    conn.close()

    return row