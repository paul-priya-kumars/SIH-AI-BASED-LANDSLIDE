from core.task_database import (
    initialize_assignments_table,
    add_assignment,
    list_assignments,
    complete_assignment
)


def create_assignment(
    title,
    subject="",
    description="",
    due_date=None,
    priority="medium"
):
    initialize_assignments_table()

    assignment_id = add_assignment(
        title=title,
        subject=subject,
        description=description,
        due_date=due_date,
        priority=priority
    )

    return assignment_id


def get_all_assignments():
    initialize_assignments_table()
    return list_assignments()


def mark_assignment_complete(assignment_id):
    initialize_assignments_table()
    complete_assignment(assignment_id)


if __name__ == "__main__":
    initialize_assignments_table()

    print("=== JARVIS ASSIGNMENT MANAGER TEST ===")

    assignment_id = create_assignment(
        title="Algebra Homework",
        subject="Math",
        description="Complete the assigned algebra problems",
        due_date="2026-09-07",
        priority="high"
    )

    print(f"\nCreated assignment ID: {assignment_id}")

    print("\nCurrent assignments:")

    for assignment in get_all_assignments():
        print(assignment)

    print("\nCompleting test assignment...")

    mark_assignment_complete(assignment_id)

    print("\nAssignments after completion:")

    for assignment in get_all_assignments():
        print(assignment)

    print("\nAssignment Manager test complete.")