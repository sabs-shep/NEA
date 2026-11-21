class KnowledgeEntry:
    def __init__(self, entry_type: str, ref_id: str):
        self._type = entry_type
        self._id = ref_id

    # Getters
    def get_type(self) -> str:
        return self._type

    def get_id(self) -> str:
        return self._id

    # Setters
    def set_type(self, entry_type: str):
        self._type = entry_type

    def set_id(self, ref_id: str):
        self._id = ref_id
