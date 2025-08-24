import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz
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
# HELPERS
# -----------------------------
def get_lists(service):
    result = service.tasklists().list(maxResults=100).execute()
    return result.get("items", [])

def print_lists(lists):
    print("📋 Current Google Task Lists:")
    for l in lists:
        print(f"- {l['title']}  (ID: {l['id']})")
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
    """Copy the task to target list first, then delete original."""
    if src_list == target_list:
        return
    body = {k: v for k, v in task.items() if k not in ("id", "etag", "selfLink")}
    inserted = service.tasks().insert(tasklist=target_list, body=body).execute()
    print(f"🔄 Moved task '{task.get('title')}' to list ID {target_list}")
    service.tasks().delete(tasklist=src_list, task=task["id"]).execute()

def redistribute_tasks(service, lists, today_id, tomorrow_id, weekday_id, my_tasks_id):
    """Move tasks from all dynamic lists (except My Tasks) to correct lists."""
    dynamic_lists = [l for l in lists if l["id"] not in (my_tasks_id,)]
    today = datetime.now(berlin_tz).date()

    for l in dynamic_lists:
        tasks = service.tasks().list(tasklist=l["id"]).execute().get("items", [])
        for task in tasks:
            due_str = task.get("due")
            if not due_str:
                continue
            due_date = iso_to_date(due_str)
            delta = (due_date - today).days

            if delta <= 0:
                target = today_id
            elif delta == 1:
                target = tomorrow_id
            elif delta == 2:
                target = weekday_id
            else:
                target = my_tasks_id

            move_task_safe(service, task, l["id"], target)

# -----------------------------
# MAIN LOGIC
# -----------------------------
def main():
    lists = get_lists(service)
    print_lists(lists)

    # Step 1: Ensure base lists exist
    today_id = ensure_list(service, lists, "Today")
    tomorrow_id = ensure_list(service, lists, "Tomorrow")
    my_tasks_id = ensure_list(service, lists, "My Tasks")  # permanent catch-all

    # Step 2: Detect existing weekday list (anything not Today/Tomorrow/My Tasks)
    weekday_list = None
    for l in lists:
        if l["title"] not in ("Today", "Tomorrow", "My Tasks"):
            weekday_list = l
            break

    # Step 3: Calculate new weekday name (day after tomorrow)
    today = datetime.now(berlin_tz).date()
    day_after = today + timedelta(days=2)
    new_weekday_name = day_after.strftime("%A")  # e.g., Thursday

    # Step 4: Rename weekday list if needed, or create it
    if weekday_list:
        if weekday_list["title"] != new_weekday_name:
            print(f"🔄 Renaming list '{weekday_list['title']}' -> '{new_weekday_name}'")
            service.tasklists().patch(
                tasklist=weekday_list["id"],
                body={"title": new_weekday_name}
            ).execute()
        weekday_id = weekday_list["id"]
    else:
        weekday_id = create_list(service, new_weekday_name)

    # Step 5: Redistribute all tasks (including tasks in Today/Tomorrow/Weekday)
    redistribute_tasks(service, lists, today_id, tomorrow_id, weekday_id, my_tasks_id)

    print("✅ Lists updated and tasks safely redistributed.")
    print(f"👉 Lists in view: Today, Tomorrow, {new_weekday_name}, My Tasks")

if __name__ == "__main__":
    main()
