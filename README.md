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

For production use, set the token as an environment variable:

```bash
# Extract token content and set as environment variable
export GOOGLE_TASKS_TOKEN="$(cat token.json)"
```

Or add it to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
echo 'export GOOGLE_TASKS_TOKEN="$(cat /path/to/your/project/token.json)"' >> ~/.zshrc
```

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
3. **Task Processing**: Examines all tasks in "My Tasks" list
4. **Date-Based Moving**: Moves tasks to appropriate lists based on due dates:
   - Overdue or today's tasks → "Today"
   - Tomorrow's tasks → "Tomorrow" 
   - Day after tomorrow's tasks → Weekday list (e.g., "Wednesday")
   - Future tasks → Remain in "My Tasks"

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
├── .github/
│   └── workflows/
│       └── tasks.yml           # GitHub Actions workflow
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

- `client_secret.json` and `token.json` are gitignored for security
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

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source. Feel free to use and modify as needed.