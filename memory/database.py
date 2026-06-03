import sqlite3

DB_NAME = "memory/research.db"


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

    conn.commit()
    conn.close()

def save_research(
    query,
    route,
    report
):

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO research_history
        (
            query,
            route,
            report
        )
        VALUES (?, ?, ?)
        """,
        (
            query,
            route,
            report
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
            timestamp
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