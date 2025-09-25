import json
import sys
from models.pydantic_models import InstanceData


class PydanticParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            instance = InstanceData.model_validate(data)

            return instance

        except FileNotFoundError:
            print(f"File not found: {self.file_path}")
            sys.exit(1)
        except PermissionError:
            print(f"Permission denied when accessing: {self.file_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Pydantic validation error: {e}")
            sys.exit(1)
