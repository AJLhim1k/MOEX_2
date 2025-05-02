import json
import os

file_path = "./questions/list.json"
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' does not exist!")
elif os.path.getsize(file_path) == 0:
    print(f"Error: File '{file_path}' is empty!")
else:
    try:
        with open(file_path, "r") as f:
            a = json.load(f)
            print(a)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in file: {e}")