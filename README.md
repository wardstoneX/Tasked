# Google Tasks Daily Organizer

A Python automation tool that organizes your Google Tasks into daily lists (Today, Tomorrow, and the day after) based on due dates. Perfect for maintaining a clean, time-based task management system.

## What It Does

This tool automatically:
- Creates and manages four task lists: "Today", "Tomorrow", a weekday list (e.g., "Wednesday"), and "My Tasks"
- Moves tasks from "My Tasks" to appropriate daily lists based on their due dates
- Renames the weekday list to always represent the day after tomorrow
- Keeps your Google Tasks organized by time horizon

## Features

- **Smart List Management**: Automatically creates missing lists and renames the weekday list
- **Date-Based Organization**: Tasks are moved based on their due dates relative to today
- **Safe Task Moving**: Tasks are copied to the target list before deletion to prevent data loss
- **Timezone Aware**: Uses Berlin timezone (easily configurable)
- **Environment Variable Support**: Secure token management via environment variables
- **Task Templates**: Automatically creates recurring tasks with subtasks based on configurable templates

## Prerequisites

- Python 3.7+
- Google account with Google Tasks enabled
- Google Cloud Project with Tasks API enabled

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks API
4. Create credentials (OAuth 2.0 Client ID) for a desktop application
5. Download the credentials JSON file and save it as `client_secret.json` in the project root

### 3. Generate Authentication Token

Run the token generation script to authenticate with Google:

```bash
python generate_token.py
```

This will:
- Open your browser for Google authentication
- Generate a `token.json` file with your credentials

### 4. Set Environment Variable

Create a `.env` file in the project root to store your token securely:

```bash
# Create .env file with your token
echo "GOOGLE_TASKS_TOKEN=$(cat token.json)" > .env
```

Your `.env` file should look like this:

```
GOOGLE_TASKS_TOKEN={"token": "your-token-here", "refresh_token": "your-refresh-token", ...}
```

**Note**: The `.env` file is already included in `.gitignore` to prevent accidental commits.

## Usage

### Manual Execution

Run the task organizer:

```bash
python move_tasks.py
```

### Automated Execution

#### Option 1: GitHub Actions (Recommended)

This project includes a GitHub Actions workflow that runs automatically:

- **Daily at 2 AM Berlin time** (midnight UTC during standard time)
- **Manual trigger** available via GitHub's "Actions" tab

To set up GitHub Actions automation:

1. Fork or create this repository on GitHub
2. Go to Settings → Secrets and variables → Actions
3. Add a new repository secret named `GOOGLE_TASKS_TOKEN`
4. Set the value to the contents of your `token.json` file
5. The workflow will run automatically according to the schedule

#### Option 2: Local Cron Job

Set up a cron job to run locally (example: every hour):

```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /path/to/your/project && /usr/bin/python3 move_tasks.py
```

## How It Works

1. **List Detection**: Identifies existing task lists and creates missing ones
2. **Weekday Management**: Renames the weekday list to represent the day after tomorrow
3. **Task Redistribution**: Moves existing tasks between lists based on their due dates:
   - Overdue or today's tasks → "Today"
   - Tomorrow's tasks → "Tomorrow" 
   - Day after tomorrow's tasks → Weekday list (e.g., "Wednesday")
   - Future tasks → "My Tasks"
4. **Template Processing**: Creates recurring tasks from templates based on weekday rules

## Task Templates

The tool supports recurring task templates that automatically create tasks with subtasks on specific days. Templates are defined in `task_templates.json`.

### Template Structure

```json
{
    "recurrence_templates": [
        {
            "title": "Daily Chores",
            "weekday": "Everyday",
            "subtasks": [
                "Make bed",
                "Clean kitchen",
                "Feed pets"
            ]
        },
        {
            "title": "Sunday Chores",
            "weekday": "Sunday",
            "subtasks": [
                "Laundry",
                "Vacuum living room",
                "Water plants"
            ]
        }
    ]
}
```

### Template Properties

- **title**: The main task name that will appear in your task lists
- **weekday**: When to create this task:
  - `"Everyday"`: Creates the task in Today, Tomorrow, and the day-after lists
  - `"Monday"`, `"Tuesday"`, etc.: Creates the task only when that day appears in your lists
- **subtasks**: Array of subtask titles that will be created under the main task

### How Templates Work

1. **Smart Creation**: Templates only create tasks that don't already exist
2. **Parent-Child Structure**: Main task becomes the parent, subtasks are nested underneath
3. **Daily Processing**: Each time the script runs, it ensures templates are present in the appropriate lists
4. **No Duplicates**: If a template task already exists, it won't be recreated

### Customizing Templates

Edit `task_templates.json` to add your own recurring tasks:

```json
{
    "recurrence_templates": [
        {
            "title": "Morning Routine",
            "weekday": "Everyday",
            "subtasks": [
                "Exercise",
                "Meditation",
                "Review daily goals"
            ]
        },
        {
            "title": "Weekly Planning",
            "weekday": "Monday",
            "subtasks": [
                "Review last week",
                "Set weekly priorities",
                "Schedule important meetings"
            ]
        }
    ]
}
```

## Configuration

### Timezone

To change the timezone, modify this line in `move_tasks.py`:

```python
berlin_tz = pytz.timezone("Europe/Berlin")  # Change to your timezone
```

### List Names

To customize list names, modify the ensure_list calls in the main() function:

```python
today_id = ensure_list(service, lists, "Today")        # Change "Today"
tomorrow_id = ensure_list(service, lists, "Tomorrow")  # Change "Tomorrow"
my_tasks_id = ensure_list(service, lists, "My Tasks")  # Change "My Tasks"
```

## File Structure

```
.
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── generate_token.py            # Authentication setup script
├── move_tasks.py               # Main task organizer script
├── task_templates.json         # Recurring task templates configuration
├── .github/
│   └── workflows/
│       └── tasks.yml           # GitHub Actions workflow
├── .env                        # Environment variables (you create)
├── client_secret.json          # Google API credentials (you provide)
├── token.json                  # Generated auth token (gitignored)
└── .gitignore                 # Git ignore rules
```

## GitHub Actions Setup

The included workflow (`.github/workflows/tasks.yml`) provides automated execution:

- **Schedule**: Runs daily at 2 AM Berlin time (midnight UTC)
- **Manual Trigger**: Can be triggered manually from GitHub Actions tab
- **Environment**: Uses Ubuntu latest with Python 3.11
- **Security**: Reads token from GitHub repository secrets

### Setting Up GitHub Actions

1. **Add Repository Secret**:
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GOOGLE_TASKS_TOKEN`
   - Value: Contents of your `token.json` file

2. **Verify Workflow**:
   - Check the "Actions" tab in your repository
   - The workflow should appear and run according to schedule
   - You can manually trigger it using "Run workflow"

## Security Notes

- `client_secret.json`, `token.json`, and `.env` are gitignored for security
- Use `.env` file for local development to keep tokens secure
- GitHub Actions uses repository secrets for secure token storage
- Tokens have limited scope (only Google Tasks access)
- Consider using service accounts for server deployments
- Never commit authentication tokens to version control

## Troubleshooting

### Authentication Issues
- Ensure `client_secret.json` is in the project root
- Re-run `generate_token.py` if authentication fails
- Check that the Google Tasks API is enabled in your Google Cloud project

### Permission Errors
- Verify the OAuth scope includes `https://www.googleapis.com/auth/tasks`
- Ensure your Google account has access to Google Tasks

### Task Moving Issues
- Check that tasks have due dates set
- Verify timezone settings match your location
- Ensure "My Tasks" list exists and contains tasks

### Template Issues
- Verify `task_templates.json` exists and has valid JSON syntax
- Check that weekday names match exactly (e.g., "Monday", not "monday")
- Ensure template tasks aren't being manually deleted before the script runs
- Templates with `"Everyday"` will appear in Today, Tomorrow, and the weekday list

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source. Feel free to use and modify as needed.