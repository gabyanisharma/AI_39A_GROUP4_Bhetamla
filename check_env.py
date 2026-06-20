import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv(override=True)

print("--- Environment Variables Detected ---")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")

if not os.getenv('DB_PASSWORD'):
    print("WARNING: DB_PASSWORD is empty!")
else:
    print("SUCCESS: DB_PASSWORD is loaded.")
