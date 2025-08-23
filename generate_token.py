from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ['https://www.googleapis.com/auth/tasks']

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save token JSON
with open('token.json', 'w') as f:
    f.write(creds.to_json())
