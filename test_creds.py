import json
import os

cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
print(f"Credential path: {cred_path}")

try:
    with open(cred_path, 'r') as f:
        cred_data = json.load(f)
    print("Credentials loaded successfully")
    print(f"Project ID: {cred_data.get('project_id')}")
except FileNotFoundError:
    print(f"File not found: {cred_path}")
except json.JSONDecodeError:
    print("File exists but is not valid JSON")
except Exception as e:
    print(f"An error occurred: {str(e)}")