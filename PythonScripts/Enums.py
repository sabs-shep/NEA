from enum import Enum

class Priority(Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    URGENT = "Urgent"
    def __str__(self):
        return self.value

class Recurrence(Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"
    NONE = None
    def __str__(self):
        return self.value if self.value != None else "None"

