import json, hashlib
from pathlib import Path

class DSRegistry:
    def __init__(self, db_path="registry.json"):
        self.path = Path(db_path)
        self.db = json.loads(self.path.read_text()) if self.path.exists() else {}

    def commit(self, symbolic_id, handle):
        key = hashlib.sha3_256(symbolic_id.encode()).hexdigest()
        self.db[key] = {"symbolic_id": symbolic_id, "handle": handle}
        self.path.write_text(json.dumps(self.db, indent=2))

    def resolve(self, symbolic_id):
        key = hashlib.sha3_256(symbolic_id.encode()).hexdigest()
        return self.db.get(key, None)
