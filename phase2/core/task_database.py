import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "jarvis_tasks.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            due_date TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_task(
    title,
    description="",
    due_date=None,
    priority="medium"
):
    connection = get_connection()

    created_at = datetime.now().isoformat(timespec="seconds")

    cursor = connection.execute(
        """
        INSERT INTO tasks
        (title, description, due_date, priority, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (title, description, due_date, priority, created_at)
    )

    task_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return task_id


def list_tasks():
    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT id, title, description, due_date,
               priority, status, created_at
        FROM tasks
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END,
            due_date
        """
    )

    tasks = cursor.fetchall()
    connection.close()

    return tasks
def initialize_assignments_table():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT DEFAULT '',
            description TEXT DEFAULT '',
            due_date TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_assignment(
    title,
    subject="",
    description="",
    due_date=None,
    priority="medium"
):
    initialize_assignments_table()

    connection = get_connection()

    created_at = datetime.now().isoformat(timespec="seconds")

    cursor = connection.execute(
        """
        INSERT INTO assignments
        (title, subject, description, due_date, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            title,
            subject,
            description,
            due_date,
            priority,
            created_at
        )
    )

    assignment_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return assignment_id


def list_assignments():
    initialize_assignments_table()

    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT id, title, subject, description,
               due_date, priority, status, created_at
        FROM assignments
        ORDER BY due_date
        """
    )

    assignments = cursor.fetchall()

    connection.close()

    return assignments


def complete_assignment(assignment_id):
    initialize_assignments_table()

    connection = get_connection()

    connection.execute(
        """
        UPDATE assignments
        SET status = 'completed'
        WHERE id = ?
        """,
        (assignment_id,)
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()

    task_id = add_task(
        title="Test JARVIS Task",
        description="Testing the Phase 2 task database",
        due_date="2026-09-05",
        priority="high"
    )

    print(f"Database created: {DATABASE_PATH}")
    print(f"Test task created with ID: {task_id}")
    print("\nTasks:")

    for task in list_tasks():
        print(task)