import os
import json
from typing import Generator

class ConfigReader:
    config_dir:str
    
    def __init__(self, dir:str):
        self.config_dir = dir
        
    def config_gen(self) -> Generator[dict, None, None]:
        for config_path in os.listdir(self.config_dir):
            if not config_path.endswith(".json"):
                continue
        
            if not os.path.exists(os.path.join(self.config_dir, config_path)):
                raise FileNotFoundError
            
            with open(os.path.join(self.config_dir, config_path), "r", encoding="utf-8") as file:
                config = json.load(file)
                yield config