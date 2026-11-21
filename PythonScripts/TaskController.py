import os
import json
from datetime import datetime
from Controller import Controller
from Task import Task
from Enums import Priority, Recurrence
import re


class TaskController(Controller):

    ### INITIALISATION
    def __init__(self, name: str = "Task"):
        super().__init__(name)
        self.tasks_dir = os.path.join(self.base_dir, "Tasks")
        os.makedirs(self.tasks_dir, exist_ok=True)

        self.tasks: list[Task] = []   # ALWAYS sorted by UUID
        self.initialise_tasks()

    ### LOADERS
    def initialise_tasks(self):
        self.tasks.clear()

        for file in os.listdir(self.tasks_dir):
            if not file.endswith(".json"):
                continue

            path = os.path.join(self.tasks_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            t = Task(
                title=data["title"],
                description=data["description"],
                priority=Priority(data["priority"]),
                due_date=datetime.fromisoformat(data["due_date"]) if data["due_date"] else None,
                reccurs=(Recurrence(data["reccurance"][0]), data["reccurance"][1]),
                tags=data["tags"]
            )

            t.id = data["id"]
            t.complete = data["complete"]
            self.tasks.append(t)

        # Sort by UUID internally
        self.tasks = self.quick_sort(self.tasks, key=lambda t: t.id)

    def load_tasks(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.tasks.clear()

        for entry in data:
            t = Task(
                title=entry["title"],
                description=entry["description"],
                priority=Priority(entry["priority"]),
                due_date=datetime.fromisoformat(entry["due_date"]) if entry["due_date"] else None,
                reccurs=(Recurrence(entry["reccurance"][0]), entry["reccurance"][1]),
                tags=entry["tags"]
            )
            t.id = entry["id"]
            t.complete = entry["complete"]
            self.tasks.append(t)

        # Sort by UUID internally
        self.tasks = self.quick_sort(self.tasks, key=lambda t: t.id)

    ### SAVERS
    def save_tasks(self):
        for t in self.tasks:
            t.to_JSON()

    ### CRUD
    def add_task(self, title, description, priority, due_date, recurrence, interval, tags, complete, kb = None):
        # Convert fields to proper types
        pr = Priority[priority]
        rec_type = Recurrence[recurrence]
        due = datetime.fromisoformat(due_date) if due_date else None
        title = f"{title}"
        if tags is None:
            tags = []
        else:
            tags = list(tags)

            
        # Create task
        t = Task(
            title=title,
            description=description,
            priority=pr,
            due_date=due,
            reccurs=[rec_type, interval],
            tags=tags
        )
        t.complete = complete

        # Save JSON
        t.to_JSON()

        # Insert by UUID
        self.insert_task_by_uuid(t)

        if kb is not None:
            kb.add_entry("Task", t.id)

        return t

    def edit_task(self, id: str, updates: dict):
        task = self.get_task(id)
        if not task:
            return False

        # Apply updates
        for key, value in updates.items():
            if key == "id":
                continue

            if key == "due_date":
                if isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(task, key, value)
                continue

            if key == "priority":
                if isinstance(value, (str, int)):
                    value = Priority[value]
                setattr(task, key, value)
                continue

            if key == "reccurance":
                rec_type, interval = value
                if isinstance(rec_type, str):
                    rec_type = Recurrence[rec_type].value
                setattr(task, key, [rec_type, interval])
                continue

            if key == "tags":
                # Convert .NET string[] → Python list
                if value is None:
                    value = []
                else:
                    value = list(value)
                setattr(task, key, value)
                continue

        # Save JSON
        task.to_JSON()

        # Reinsert by UUID
        self.tasks.remove(task)
        self.insert_task_by_uuid(task)

        return True

    def delete_task(self, id: str, kb = None):
        task = self.get_task(id)
        if not task:
            return False

        path = os.path.join(self.tasks_dir, f"{id}.json")
        if os.path.exists(path):
            os.remove(path)

        if kb is not None:
            kb.remove_entry("Task", id)

        self.tasks.remove(task)
        return True

    ### GETTERS
    def get_task(self, id: str):
        # Binary search by UUID
        low, high = 0, len(self.tasks)

        while low < high:
            mid = (low + high) // 2
            mid_id = self.tasks[mid].id

            if mid_id == id:
                return self.tasks[mid]
            elif mid_id < id:
                low = mid + 1
            else:
                high = mid

        return None
    def get_task_as_dict(self, id: str):
        task = self.get_task(id)
        if task is None:
            return None

        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority.value,
            "tags": task.tags,
            "reccurance": task.reccurance,
            "complete": task.complete
        }


    def get_all_tasks(self):
        # UI wants alphabetical order
        return self.quick_sort(self.tasks.copy(), key=lambda t: t.title.lower())

    ### BASIC SEARCH HELPERS
    def search_by_title(self, title: str):
        title = title.lower()
        return [t for t in self.tasks if title in t.title.lower()]

    def search_by_description(self, text: str):
        text = text.lower()
        return [t for t in self.tasks if text in t.description.lower()]

    def search_by_tags(self, tag: str):
        tag = tag.lower()
        return [t for t in self.tasks if any(tag in tg.lower() for tg in t.tags)]

    ### PHRASE SEARCH
    def search_tasks(self, query: str, ai_controller=None):
        query = query.lower().strip()
        words = [w for w in query.split(" ") if w]

        if not words:
            return []

        phrases = self._generate_phrases(words)

        ## title search
        for p in phrases:
            hits = self.search_by_title(p)
            if hits:
                return hits

        ## description search
        for p in phrases:
            hits = self.search_by_description(p)
            if hits:
                return hits

        ## tag search
        for p in phrases:
            hits = self.search_by_tags(p)
            if hits:
                return hits

        ### AI SEARCH
        if ai_controller is not None:
            ai_result = self.ai_infer_search(query, self.tasks, ai_controller)

            ## sanity check
            if not isinstance(ai_result, dict):
                return []

            suggested_ids = ai_result.get("suggested_tasks", [])
            keywords_for_tasks = ai_result.get("keywords_for_tasks", {})
            keywords_for_query = ai_result.get("keywords_for_query", [])

            inferred = []

            ## convert IDs → Task objects
            for tid in suggested_ids:
                task = self.get_task(tid)
                if task:
                    inferred.append(task)

            ## apply per‑task tags
            for tid, new_tags in keywords_for_tasks.items():
                task = self.get_task(tid)
                if task:
                    self.apply_keyword_learning(new_tags, [task])

            ## also learn query‑level tags on all inferred tasks
            if inferred and keywords_for_query:
                self.apply_keyword_learning(keywords_for_query, inferred)

            ## persist updated tags
            self.save_tasks()

            return inferred

        return []

    def _generate_phrases(self, words: list[str]):
        phrases = []
        n = len(words)

        phrases.append(" ".join(words[0:n]))

        for i in range(0, 2):
            for j in range(n - 1, n + 1):
                if 0 <= i < j <= n:
                    phrases.append(" ".join(words[i:j]))

        for i in range(0, 3):
            for j in range(n - 2, n + 1):
                if 0 <= i < j <= n:
                    phrases.append(" ".join(words[i:j]))

        for w in words:
            phrases.append(w)

        seen = set()
        clean = []
        for p in phrases:
            if p not in seen and p != "":
                seen.add(p)
                clean.append(p)

        return clean

    ### SORTERS
    def sort_by_title(self):
        arr = self.tasks.copy()
        return self.quick_sort(arr, key=lambda t: t.title.lower())

    def sort_by_priority(self):
        arr = self.tasks.copy()

        priority_order = {
            "Low": 1,
            "Normal": 2,
            "High": 3,
            "Urgent": 4
        }

        return self.quick_sort(arr, key=lambda t: priority_order[t.priority.value])

    def sort_by_due_date(self):
        arr = self.tasks.copy()
        return self.quick_sort(arr, key=lambda t: t.due_date or datetime.max)

    def sort_by_created(self):
        arr = self.tasks.copy()
        return self.quick_sort(arr, key=lambda t: getattr(t, "created_at", datetime.min))

    ### INSERTION / SORTING
    def insert_task_by_uuid(self, task: Task):
        tid = task.id
        low, high = 0, len(self.tasks)

        while low < high:
            mid = (low + high) // 2
            if self.tasks[mid].id < tid:
                low = mid + 1
            else:
                high = mid

        self.tasks.insert(low, task)

    def quick_sort(self, arr, key=lambda x: x):
        if len(arr) <= 1:
            return arr

        pivot = key(arr[len(arr) // 2])
        left = [x for x in arr if key(x) < pivot]
        mid = [x for x in arr if key(x) == pivot]
        right = [x for x in arr if key(x) > pivot]

        return self.quick_sort(left, key) + mid + self.quick_sort(right, key)


    ### AI HOOKS
    def ai_infer_search(self, user_query: str, tasks: list[Task], aiController):
        ### BUILD TASK PAYLOAD
        # Convert Task objects into JSON‑serialisable dictionaries
        tasks_payload = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "tags": t.tags,
                "priority": t.priority.value
            }
            for t in tasks
        ]

        ### BUILD PROMPT
        prompt = f"""
    You are a semantic task search engine.

    ### USER QUERY
    {user_query}

    ### TASK LIST
    {json.dumps(tasks_payload, indent=2)}

    ### TASK
    Identify which tasks are semantically related to the user query.

    Return ONLY valid JSON in this exact structure:

    {{
    "suggested_tasks": ["uuid1", "uuid2"],
    "keywords_for_tasks": {{
        "uuid1": ["tag1", "tag2"],
        "uuid2": ["tag3"]
    }},
    "keywords_for_query": ["tagA", "tagB"]
    }}

    Rules:
    - Do NOT include chain-of-thought.
    - Do NOT explain.
    - Do NOT add fields.
    - If no tasks match, return empty lists.
    """.strip()

        ### CALL AI CONTROLLER
        raw = aiController.send_message(prompt, think=False, search=False)

        print("Raw AI response:", raw)  # DEBUG

        ### EXTRACT JSON BLOCK
        # AI has already removed everything up to </think>
        # extract_json_block() handles markdown fences + JSON isolation
        data = self.extract_json_block(raw)

        ### VALIDATE STRUCTURE
        if not isinstance(data, dict):
            return {
                "suggested_tasks": [],
                "keywords_for_tasks": {},
                "keywords_for_query": []
            }

        ### NORMALISE AND RETURN
        return {
            "suggested_tasks": data.get("suggested_tasks", []),
            "keywords_for_tasks": data.get("keywords_for_tasks", {}),
            "keywords_for_query": data.get("keywords_for_query", [])
        }

    def extract_json_block(self, raw: str) -> dict:
        # Remove markdown fences
        raw = raw.replace("```json", "").replace("```", "")

        # Find the first {...} block
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            return {}

        json_str = m.group(0)

        try:
            return json.loads(json_str)
        except:
            return {}

    ### KEYWORD LEARNING (merge tags safely)
    def apply_keyword_learning(self, new_tags: list[str], tasks: list[Task]):
        clean_tags = []
        for tag in new_tags:
            if not isinstance(tag, str):
                continue
            t = tag.strip().lower()
            if t and t not in clean_tags:
                clean_tags.append(t)

        for task in tasks:
            if not hasattr(task, "tags") or task.tags is None:
                task.tags = []

            existing = {t.lower() for t in task.tags if isinstance(t, str)}
            for tag in clean_tags:
                if tag not in existing:
                    task.tags.append(tag)
                    existing.add(tag)

            task.to_JSON()