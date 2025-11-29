import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Storage(ABC):
    @abstractmethod
    def save(self, data: Dict[str, List[Dict[str, Any]]]):
        pass

    @abstractmethod
    def load(self) -> Dict[str, List[Dict[str, Any]]]:
        pass

class JsonStorage(Storage):
    def __init__(self, file_path: str = "catalog.json"):
        self.file_path = file_path

    def save(self, data: Dict[str, List[Dict[str, Any]]]):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self) -> Dict[str, List[Dict[str, Any]]]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
