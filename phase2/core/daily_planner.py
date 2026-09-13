from datetime import datetime, date

from core.task_manager import get_all_tasks
from core.assignment_manager import get_all_assignments


def get_today():
    return date.today().isoformat()


def get_daily_plan(target_date=None):
    if target_date is None:
        target_date = get_today()

    tasks = get_all_tasks()
    assignments = get_all_assignments()

    plan = {
        "date": target_date,
        "tasks": [],
        "assignments": []
    }

    for task in tasks:
        due_date = task[3]
        status = task[5]

        if status != "completed" and (
            due_date is None or due_date <= target_date
        ):
            plan["tasks"].append(task)

    for assignment in assignments:
        due_date = assignment[4]
        status = assignment[6]

        if status != "completed" and (
            due_date is None or due_date <= target_date
        ):
            plan["assignments"].append(assignment)

    return plan


def print_daily_plan(target_date=None):
    plan = get_daily_plan(target_date)

    print(f"\n=== JARVIS DAILY PLAN ===")
    print(f"Date: {plan['date']}")

    print("\nTasks:")

    if plan["tasks"]:
        for task in plan["tasks"]:
            print(
                f"- [{task[4].upper()}] "
                f"{task[1]} "
                f"(Due: {task[3] or 'No due date'})"
            )
    else:
        print("- No pending tasks")

    print("\nAssignments:")

    if plan["assignments"]:
        for assignment in plan["assignments"]:
            print(
                f"- [{assignment[5].upper()}] "
                f"{assignment[1]} "
                f"({assignment[2] or 'No subject'}) "
                f"(Due: {assignment[4] or 'No due date'})"
            )
    else:
        print("- No pending assignments")


if __name__ == "__main__":
    print_daily_plan()