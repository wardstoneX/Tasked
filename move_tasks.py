import os
import json
from datetime import date, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz

# -----------------------------
# CONFIG
# -----------------------------
DAY_LISTS = [
    "LIST_ID_SLOT_0",  # Today
    "LIST_ID_SLOT_1",  # Tomorrow
    "LIST_ID_SLOT_2",
    "LIST_ID_SLOT_3",
    "LIST_ID_SLOT_4",
    "LIST_ID_SLOT_5",
    "LIST_ID_SLOT_6"
]

OTHER_TASKS_LIST = "OTHER_TASKS_LIST_ID"

# -----------------------------
# AUTHENTICATION
# -----------------------------
token_json = os.environ['GOOGLE_TASKS_TOKEN']
token_data = json.loads(token_json)
creds = Credentials.from_authorized_user_info(token_data, ['https://www.googleapis.com/auth/tasks'])
service = build('tasks', 'v1', credentials=creds)

# -----------------------------
# HELPERS
# -----------------------------
def iso_to_date(iso_str):
    return datetime.fromisoformat(iso_str.replace('Z','+00:00')).date()

def move_task(task, target_list_id):
    """Move a task to another list (copy then delete)"""
    task_body = task.copy()
    task_body.pop('id', None)
    task_body.pop('etag', None)
    task_body.pop('selfLink', None)
    service.tasks().insert(tasklist=target_list_id, body=task_body).execute()
    service.tasks().delete(tasklist=task['tasklist_id'], task=task['id']).execute()

# -----------------------------
# MAIN LOGIC
# -----------------------------
berlin_tz = pytz.timezone("Europe/Berlin")
today_berlin = datetime.now(berlin_tz).date()

# Fetch tasks from Other Tasks
other_tasks = service.tasks().list(tasklist=OTHER_TASKS_LIST).execute().get('items', [])

for task in other_tasks:
    task['tasklist_id'] = OTHER_TASKS_LIST
    due_str = task.get('due')
    if not due_str:
        continue
    due_date = iso_to_date(due_str)
    delta = (due_date - today_berlin).days

    if delta < 0:
        slot = 0  # Overdue → Today
    elif delta > 6:
        continue  # Leave in Other Tasks
    else:
        slot = delta  # 0 → Today, 1 → Tomorrow, etc.

    target_list_id = DAY_LISTS[slot]
    
    # Only move if not already in correct list
    if task['tasklist_id'] != target_list_id:
        move_task(task, target_list_id)

print("Task redistribution completed. All tasks are in the correct lists.")
