import json

def read_config(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as fs:
            return json.load(fs) # channelSecret & accessToken
    except FileNotFoundError:
        print('failed to load credential')
        quit("the LINE bot API is terminated")