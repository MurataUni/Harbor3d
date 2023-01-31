from dataclasses import dataclass

from typing import Dict
import json

@dataclass
class JsonLoader:
    file:str
    dictionary:Dict = None

    def load(self):
        with open(self.file) as f:
            self.dictionary = json.load(f)
    
    def fetch(self):
        if self.dictionary == None:
            self.load()
        return self.dictionary
    
    def dump(self):
        with open(self.file, 'wt') as f:
            json.dump(self.dictionary, f, indent=2)
