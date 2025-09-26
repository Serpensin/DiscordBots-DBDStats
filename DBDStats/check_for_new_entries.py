import re
import requests

ignored_keys = ["steamid", "hash", "banstate", "survivor_ultrarare", "killer_ultrarare"]

def extract_keys_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    keys = re.findall(r'["\']([a-zA-Z0-9_]+)["\']', content)
    return set(keys)

def load_json_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def compare_keys(file_path, url):
    file_keys = extract_keys_from_file(file_path)
    json_data = load_json_from_url(url)
    json_keys = set(json_data.keys())

    json_keys -= set(ignored_keys)

    missing_in_file = json_keys - file_keys

    print("Keys, die in der JSON sind, aber nicht in der Datei:")
    for key in missing_in_file:
        print(key)

    return missing_in_file

file_path = "main.py"
json_url = "https://dbd.tricky.lol/api/playerstats?steamid=76561198424893695"

missing_keys = compare_keys(file_path, json_url)

with open("missing_keys.txt", "w", encoding="utf-8") as output_file:
    for key in missing_keys:
        output_file.write(f"{key}\n")
