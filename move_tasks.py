import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz

# dotenv is needed only for local runs
#from dotenv import load_dotenv

#load_dotenv()

# -----------------------------
# AUTHENTICATION
# -----------------------------
token_json = os.environ["GOOGLE_TASKS_TOKEN"]
token_data = json.loads(token_json)
creds = Credentials.from_authorized_user_info(
    token_data, ["https://www.googleapis.com/auth/tasks"]
)
service = build("tasks", "v1", credentials=creds)

berlin_tz = pytz.timezone("Europe/Berlin")

# -----------------------------
# LOAD TEMPLATES FROM FILE
# -----------------------------
TEMPLATE_FILE = "task_templates.json"
with open(TEMPLATE_FILE, "r") as f:
    templates_data = json.load(f)

recurrence_templates = templates_data.get("recurrence_templates", [])

# -----------------------------
# HELPERS
# -----------------------------
def get_lists(service):
    result = service.tasklists().list(maxResults=100).execute()
    return result.get("items", [])

def print_lists(service, lists):
    print("📋 Current Google Task Lists:")
    for l in lists:
        print(f"- {l['title']}  (ID: {l['id']})")
        tasks = service.tasks().list(tasklist=l["id"]).execute().get("items", [])
        if not tasks:
            print("   🗒️ No tasks")
        else:
            for t in tasks:
                title = t.get("title")
                due = t.get("due", "No due date")
                if title:
                    print(f"   - {title} (Due: {due})")
    print("-" * 40)

def find_list_id(lists, name):
    for l in lists:
        if l["title"].lower() == name.lower():
            return l["id"]
    return None

def create_list(service, name):
    new_list = service.tasklists().insert(body={"title": name}).execute()
    print(f"✅ Created list: {name} (ID: {new_list['id']})")
    return new_list["id"]

def ensure_list(service, lists, name):
    lid = find_list_id(lists, name)
    if lid:
        return lid
    return create_list(service, name)

def iso_to_date(iso_str):
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).date()

def move_task_safe(service, task, src_list, target_list):
    if src_list == target_list:
        return
    body = {k: v for k, v in task.items() if k not in ("id", "etag", "selfLink")}
    service.tasks().insert(tasklist=target_list, body=body).execute()
    service.tasks().delete(tasklist=src_list, task=task["id"]).execute()
    title = task.get("title", "<no title>")
    print(f"🔄 Moved task '{title}' from list ID {src_list} to {target_list}")

def redistribute_tasks(service, lists, today_id, tomorrow_id, day_after_id, my_tasks_id):
    """Move existing tasks to correct lists according to their due date"""
    dynamic_lists = [l for l in lists if l["id"] not in (my_tasks_id,)]
    today = datetime.now(berlin_tz).date()

    for l in dynamic_lists:
        tasks = service.tasks().list(tasklist=l["id"], showCompleted=False).execute().get("items", [])
        for task in tasks:
            title = task.get("title")
            if not title:
                continue  # ignore tasks without title

            due_str = task.get("due")
            if due_str:
                due_date = iso_to_date(due_str)
                delta = (due_date - today).days
            else:
                # No due date: treat based on current list
                if l["id"] == today_id:
                    delta = 0
                elif l["id"] == tomorrow_id:
                    delta = 1
                elif l["id"] == day_after_id:
                    delta = 2
                else:
                    continue  # tasks in My Tasks or unknown list without due date -> don't roll

            if delta <= 0:
                target = today_id
            elif delta == 1:
                target = tomorrow_id
            elif delta == 2:
                target = day_after_id
            else:
                target = my_tasks_id

            move_task_safe(service, task, l["id"], target)

# -----------------------------
# TEMPLATE HANDLING WITH PARENT + SUBTASKS
# -----------------------------
def copy_task_template(service, task, target_list):
    """Create parent task and its subtasks robustly, without duplicating anything"""
    # Get all tasks in target list (excluding completed tasks)
    existing_tasks = service.tasks().list(tasklist=target_list, showCompleted=False).execute().get("items", [])

    # Ignore tasks without a title
    existing_tasks = [t for t in existing_tasks if t.get("title")]

    # Check if parent exists
    parent_task = None
    for t in existing_tasks:
        if t["title"] == task["title"] and "parent" not in t:
            parent_task = t
            break

    if parent_task:
        print(f"✔ Parent task '{task['title']}' already exists in list ID {target_list}")
    else:
        # Create parent task
        parent_task = service.tasks().insert(tasklist=target_list, body={"title": task["title"]}).execute()
        print(f"📌 Created parent task '{task['title']}' in list ID {target_list}")

    # Collect existing subtasks under parent
    existing_subtasks = []
    for t in existing_tasks:
        if t.get("parent") == parent_task["id"]:
            existing_subtasks.append(t["title"])

    # Create missing subtasks
    for sub_title in task.get("subtasks", []):
        if sub_title in existing_subtasks:
            print(f"   ↳ Subtask '{sub_title}' already exists under '{task['title']}'")
            continue
        # Insert subtask at top level first
        subtask = service.tasks().insert(tasklist=target_list, body={"title": sub_title}).execute()
        # Move it under parent
        service.tasks().move(tasklist=target_list, task=subtask["id"], parent=parent_task["id"]).execute()
        print(f"   ↳ Created subtask '{sub_title}' under '{task['title']}'")


def fill_all_lists(service, today_id, tomorrow_id, day_after_id, today_date, day_after_date):
    """Ensure templates exist in the right lists according to recurrence rules"""
    for task in recurrence_templates:
        for offset, lst, date in [(0, today_id, today_date),
                                  (1, tomorrow_id, today_date + timedelta(days=1)),
                                  (2, day_after_id, day_after_date)]:
            weekday = task.get("weekday", "")
            if weekday == "Everyday" or weekday == date.strftime("%A"):
                copy_task_template(service, task, lst)

# -----------------------------
# MAIN LOGIC
# -----------------------------
def main():
    lists = get_lists(service)
    print_lists(service, lists)

    # Ensure base lists exist
    today_id = ensure_list(service, lists, "Today")
    tomorrow_id = ensure_list(service, lists, "Tomorrow")

    today = datetime.now(berlin_tz).date()
    day_after = today + timedelta(days=2)
    day_after_name = day_after.strftime("%A")

    # Detect or create weekday list (Day After)
    weekday_list = None
    for l in lists:
        if l["title"] not in ("Today", "Tomorrow", "My Tasks"):
            weekday_list = l
            break
    if weekday_list:
        if weekday_list["title"] != day_after_name:
            print(f"🔄 Renaming list '{weekday_list['title']}' -> '{day_after_name}'")
            service.tasklists().patch(
                tasklist=weekday_list["id"],
                body={"title": day_after_name}
            ).execute()
        day_after_id = weekday_list["id"]
    else:
        day_after_id = create_list(service, day_after_name)

    # Redistribute existing tasks
    my_tasks_id = find_list_id(lists, "My Tasks") or create_list(service, "My Tasks")
    redistribute_tasks(service, lists, today_id, tomorrow_id, day_after_id, my_tasks_id)

    # Fill templates with parent + subtasks
    fill_all_lists(service, today_id, tomorrow_id, day_after_id, today, day_after)

    print("✅ Lists updated, recurring templates ensured.")
    print(f"👉 Lists in view: Today, Tomorrow, {day_after_name}")

if __name__ == "__main__":
    main()
