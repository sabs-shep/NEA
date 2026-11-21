from datetime import datetime
from Enums import Priority, Recurrence, Enum
import os
import json
import uuid


class Task:
    ### INITIALISATION
    def __init__(self, title, priority=Priority.NORMAL, description="", due_date=None,
                 reccurs=None, tags=None) -> None:

        self.id: str = str(uuid.uuid4())
        self.title: str = title
        self.description: str = description
        self.due_date: datetime | None = due_date

        # Priority is stored as ENUM
        self.priority: Enum = priority

        # Tags stored as list of strings
        self.tags: list[str] = tags if tags is not None else []

        # Recurrence ALWAYS stored as VALUE, not enum object
        # Default: ["None", 1]
        if reccurs is None:
            self.reccurance = [Recurrence.NONE.value, 1]
        else:
            # Ensure value form
            self.reccurance = [
                reccurs[0] if isinstance(reccurs[0], str) else reccurs[0].value,
                reccurs[1]
            ]

        self.complete: bool = False

        # Save path
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        base_dir = os.path.join(appdata, "NEAApp", "SaveData")
        self.JSON_path = os.path.join(base_dir, "Tasks")

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_due_date(self):
        return self.due_date

    def get_priority(self):
        return self.priority

    def get_tags(self):
        return self.tags

    # Recurrence getter ALWAYS returns (value, interval)
    def get_reccurance(self):
        return (self.reccurance[0], self.reccurance[1])

    ### SETTERS
    def set_title(self, new_title):
        self.title = new_title

    def set_description(self, new_description):
        self.description = new_description

    def set_due_date(self, new_due_date):
        self.due_date = new_due_date

    def set_priority(self, new_priority):
        self.priority = new_priority

    def clear_due_date(self):
        self.set_due_date(None)

    def add_tag(self, tags: str | list[str]):
        tags = [tags] if isinstance(tags, str) else tags
        self.tags.extend(tags)

    def remove_tag(self, tags: str | list[str]):
        tags = [tags] if isinstance(tags, str) else tags
        for tag in tags:
            if tag in self.tags:
                self.tags.remove(tag)

    # Recurrence setter ALWAYS stores value, not enum
    def set_reccurance(self, type: Enum, interval: int = 1):
        self.reccurance = [type.value, interval]

    def is_overdue(self):
        if self.due_date is None:
            return False
        return datetime.now() > self.due_date

    ### JSON SERIALISATION
    def to_JSON(self):
        os.makedirs(self.JSON_path, exist_ok=True)

        due = self.due_date.isoformat() if self.due_date else None

        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": due,
            "priority": self.priority.value,
            "tags": self.tags,
            "reccurance": [self.reccurance[0], self.reccurance[1]],
            "complete": self.complete
        }

        file_path = os.path.join(self.JSON_path, f"{self.id}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        return file_path

    

    ### LOAD FROM JSON BY UUID
    def from_JSON(self, id: str):
        file_path = os.path.join(self.JSON_path, f"{id}.json")

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception:
            try:
                os.remove(file_path)
            except:
                pass
            return None

        self.id = data["id"]
        self.title = data["title"]
        self.description = data["description"]

        self.due_date = (
            datetime.fromisoformat(data["due_date"])
            if data["due_date"] else None
        )

        # Priority restored as enum
        self.priority = Priority(data["priority"])

        # Tags sanitised
        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, str):
            if raw_tags.strip() in ("[]", ""):
                self.tags = []
            else:
                self.tags = [raw_tags]
        else:
            self.tags = [t for t in raw_tags if t not in ("[]", "", "''", "\"[]\"")]

        # Recurrence ALWAYS restored as value, not enum
        rec_value = data["reccurance"][0]
        rec_interval = data["reccurance"][1]
        self.reccurance = [rec_value, rec_interval]

        self.complete = data["complete"]

        return self
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority.value,
            "tags": self.tags,
            "reccurance": self.reccurance,
            "complete": self.complete
        }

    def __str__(self):
        return json.dumps(self.to_dict())