import os
from parser.parser import Parser

def parse_all_files(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

    if not files:
        print(f"No JSON files found in {folder_path}")
        return []

    instances = []

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        try:
            parser = Parser(file_path)
            instance = parser.parse()
            instances.append((file_name, instance))
        except FileNotFoundError:
            print(f"File not found: {file_path}. Skipping.")
        except PermissionError:
            print(f"Permission denied: {file_path}. Skipping.")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {file_path}: {e}. Skipping.")
        except KeyError as e:
            print(f"Missing required field {e} in {file_path}. Skipping.")
        except Exception as e:
            print(f"Unexpected error while parsing {file_path}: {e}. Skipping.")

    return instances
