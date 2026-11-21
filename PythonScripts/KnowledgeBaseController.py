import os
import json
from Controller import Controller
from KnowledgeEntry import KnowledgeEntry


class KnowledgeBaseController(Controller):

    ### INITIALISATION
    ## Sets up KB controller, loads JSON, registers AI + prefs
    def __init__(self, ai_controller=None, preferences_controller=None, name="KB"):
        super().__init__(name)

        self.ai_controller = ai_controller
        self.preferences = preferences_controller

        # Path: %APPDATA%/NEAApp/SaveData/KB.json
        self.json_path = os.path.join(self.base_dir, "KB.json")

        # Internal list of KnowledgeEntry objects
        self.entries: list[KnowledgeEntry] = []

        # Maps entry types → controllers (e.g., "Task" → TaskController)
        self._resolver_map: dict[str, object] = {}

        self._initialise_knowledge()

    ### PERSISTENCE FUNCTIONS
    ## Loads KB.json into memory
    def _initialise_knowledge(self):
        if not os.path.exists(self.json_path):
            self.entries = []
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.entries = []
            for d in data:
                entry = KnowledgeEntry(
                    entry_type=d["type"],
                    ref_id=d["ref_id"]
                )
                self.entries.append(entry)

        except Exception as e:
            self.handle_error(e, "loading KB.json")
            self.entries = []

    ## Saves all entries to KB.json
    def save(self):
        try:
            data = []
            for e in self.entries:
                data.append({
                    "type": e.get_type(),
                    "ref_id": e.get_id()
                })

            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            self.log("Knowledge base saved.")
        except Exception as e:
            self.handle_error(e, "saving KB.json")

    ### BASIC ENTRY MANAGEMENT
    ## Adds a lightweight reference to the knowledge base
    def add_entry(self, entry_type, ref_id):
        entry = KnowledgeEntry(entry_type, ref_id)
        self.entries.append(entry)
        self.save()
        return ref_id  # ref_id is the unique identifier

    ## Removes an entry by ref_id
    def remove_entry(self, ref_id):
        self.entries = [e for e in self.entries if e.get_id() != ref_id]
        self.save()

    ## Returns a KnowledgeEntry by ref_id
    def get_entry(self, ref_id):
        for e in self.entries:
            if e.get_id() == ref_id:
                return e
        return None

    ## Returns all entries
    def get_all_entries(self):
        return self.entries

    ## Returns all entries of a given type
    def filter_by_type(self, entry_type):
        return [e for e in self.entries if e.get_type() == entry_type]

    ### RESOLUTION LAYER
    ## Registers a controller to handle a specific entry type
    def register_type(self, type_name: str, controller):
        # skip if controller is None
        if controller is None:
            return
        if type_name in self._resolver_map:
            return
        self._resolver_map[type_name] = controller


    ## Resolves a KnowledgeEntry → actual domain object (Task, Note, etc.)
    def resolve(self, entry: KnowledgeEntry):
        controller = self._resolver_map.get(entry.get_type())
        if controller is None:
            return None

        getter_name = f"get_{entry.get_type().lower()}"
        if not hasattr(controller, getter_name):
            return None

        getter = getattr(controller, getter_name)

        try:
            return getter(entry.get_id())
        except Exception as e:
            self.handle_error(e, f"resolving {entry.get_type()}:{entry.get_id()}")
            return None

    ### INFORMATION EXPORT
    ## Returns a dictionary of all relevant fields for C# UI
    def get_information(self, ref_id):
        entry = self.get_entry(ref_id)
        if not entry:
            return {"error": "Entry not found"}

        # Resolve underlying object (Task, Note, etc.)
        self.log(f"Resolving entry {entry.get_type()}:{entry.get_id()}")
        obj = self.resolve(entry)
        if obj is None:
            return {
                "type": entry.get_type(),
                "ref_id": entry.get_id(),
                "error": "Could not resolve underlying object"
            }

        # Convert JSON string from __str__ into a dictionary
        try:
            info = json.loads(str(obj))
        except Exception as e:
            self.handle_error(e, "parsing JSON from __str__")
            return {"error": "Invalid JSON returned from object __str__"}

        # Add KB metadata (unsorted, untouched)
        info["kb_type"] = entry.get_type()
        info["kb_ref_id"] = entry.get_id()

        return info

    ### SEARCH
    ## Searches across all registered controllers and maps back to KB entries
    def search(self, query: str):
        query = (query or "").strip().lower()

        # No query → return everything
        if not query:
            return [
                {
                    "type": e.get_type(),
                    "ref_id": e.get_id(),
                    "label": f"{e.get_type()} ({e.get_id()})"
                }
                for e in self.entries
            ]

        results = []

        # Loop through each registered type (Task, Note, etc.)
        for type_name, controller in self._resolver_map.items():

            # Build the expected search function name
            search_func_name = f"search_{type_name.lower()}s"

            # If the controller doesn't have this search function, skip
            if not hasattr(controller, search_func_name):
                continue

            search_func = getattr(controller, search_func_name)

            try:
                matches = search_func(query)
            except Exception as e:
                self.handle_error(e, f"searching in {type_name}")
                continue

            # Each match is a domain object (Task, Note, etc.)
            for obj in matches:
                ref_id = getattr(obj, "id", None)
                if ref_id is None:
                    continue

                # Ensure KB entry exists
                if self.get_entry(ref_id) is None:
                    self.add_entry(type_name, ref_id)

                # Build label (title, name, etc.)
                label = getattr(obj, "title", None) or getattr(obj, "name", None) or ref_id

                results.append({
                    "type": type_name,
                    "ref_id": ref_id,
                    "label": label
                })

        return results