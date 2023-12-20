import json

def read_config(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding="utf-8") as fs:
            return json.load(fs) # channelSecret & accessToken
    except FileNotFoundError:
        quit(f"failed to load credential: {file_path}")