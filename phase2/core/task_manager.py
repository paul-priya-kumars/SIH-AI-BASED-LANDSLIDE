from core.task_database import (
    initialize_database,
    add_task,
    list_tasks,
    get_connection
)


def create_task(
    title,
    description="",
    due_date=None,
    priority="medium"
):
    initialize_database()

    task_id = add_task(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority
    )

    return task_id


def get_all_tasks():
    initialize_database()
    return list_tasks()


def complete_task(task_id):
    initialize_database()

    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET status = 'completed'
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()
    connection.close()


def delete_task(task_id):
    initialize_database()

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()
    connection.close()


def update_task(
    task_id,
    title=None,
    description=None,
    due_date=None,
    priority=None,
    status=None
):
    initialize_database()

    connection = get_connection()

    if title is not None:
        connection.execute(
            "UPDATE tasks SET title = ? WHERE id = ?",
            (title, task_id)
        )

    if description is not None:
        connection.execute(
            "UPDATE tasks SET description = ? WHERE id = ?",
            (description, task_id)
        )

    if due_date is not None:
        connection.execute(
            "UPDATE tasks SET due_date = ? WHERE id = ?",
            (due_date, task_id)
        )

    if priority is not None:
        connection.execute(
            "UPDATE tasks SET priority = ? WHERE id = ?",
            (priority, task_id)
        )

    if status is not None:
        connection.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id)
        )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()

    print("=== JARVIS TASK MANAGER TEST ===")

    task_id = create_task(
        title="Test Task Manager",
        description="Testing JARVIS task management",
        due_date="2026-09-06",
        priority="high"
    )

    print(f"\nCreated task ID: {task_id}")

    print("\nCurrent tasks:")

    for task in get_all_tasks():
        print(task)

    print("\nCompleting test task...")

    complete_task(task_id)

    print("\nTasks after completion:")

    for task in get_all_tasks():
        print(task)

    print("\nTask Manager test complete.")