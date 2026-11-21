import json
import os
import datetime
from typing import Any, Dict, List
from Controller import Controller
from RGB import RGB


class SettingsController(Controller):

    ### INITIALISATION
    def __init__(self, name: str):
        super().__init__(name)
        self.load_preferences(self._preferences_path)

        # Ensure "themes" setting exists and is well-formed
        if "themes" not in self._preferences:
            self._preferences["themes"] = {
                "category": "UI",
                "description": "Colour themes",
                "default": None,
                "current": None,
                "options": [],
                "last_updated": None,
                "previous_version": None
            }
            self._persist_preferences()
        else:
            # Ensure required fields exist
            themes = self._preferences["themes"]
            themes.setdefault("category", "UI")
            themes.setdefault("description", "Colour themes")
            themes.setdefault("default", None)
            themes.setdefault("current", None)
            themes.setdefault("options", [])
            themes.setdefault("last_updated", None)
            themes.setdefault("previous_version", None)
            self._persist_preferences()

    ### CATEGORY + QUERY FUNCTIONS
    def list_categories(self) -> List[str]:
        return list({pref.get("category", "Uncategorized") for pref in self._preferences.values()})

    def get_settings_for_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        return {k: v for k, v in self._preferences.items() if v.get("category") == category}

    ### EDITING FUNCTIONS
    def update_preference(self, key: str, value: Any) -> None:
        if key not in self._preferences:
            self._preferences[key] = {
                "category": "Uncategorized",
                "description": "",
                "default": None,
                "current": None,
                "options": [],
                "last_updated": None,
                "previous_version": None
            }

        pref = self._preferences[key]
        pref["previous_version"] = pref.get("current")
        pref["current"] = value
        pref["last_updated"] = datetime.datetime.now().isoformat()

        self._persist_preferences()
        self.log(f"Preference updated: {key} -> {value}")

    def save_theme_xaml(self, filename: str, content: str):
        theme_dir = os.path.join(self.base_dir, "Themes")
        os.makedirs(theme_dir, exist_ok=True)

        path = os.path.join(theme_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    ### RESET FUNCTIONS
    def reset_preference(self, key: str) -> None:
        if key in self._preferences:
            pref = self._preferences[key]
            pref["current"] = pref.get("default")
            pref["last_updated"] = datetime.datetime.now().isoformat()

            self._persist_preferences()
            self.log(f"Preference reset: {key} -> {pref['default']}")

    def return_to_defaults(self) -> None:
        for key, pref in self._preferences.items():
            pref["current"] = pref.get("default")
            pref["last_updated"] = datetime.datetime.now().isoformat()

        self._persist_preferences()
        self.log("All preferences returned to defaults")

    ### ACCESSORS
    def get_description(self, key: str) -> str:
        if key in self._preferences:
            return self._preferences[key].get("description", "")
        return ""

    def get_current(self, key: str) -> Any:
        if key in self._preferences:
            return self._preferences[key].get("current")
        return None

    def set_current(self, key: str, value: Any) -> None:
        self.update_preference(key, value)

    ### OPTIONS
    def add_option(self, key: str, option: Any) -> None:
        if key in self._preferences:
            options = self._preferences[key].setdefault("options", [])
            if option not in options:
                options.append(option)
                self._persist_preferences()
                self.log(f"Option added to {key}: {option}")

    def get_options(self, key: str) -> List[Any]:
        if key in self._preferences:
            return self._preferences[key].get("options", [])
        return []

    def add_option_to_setting(self, key: str, option: Any) -> None:
        self.add_option(key, option)

    def remove_option_from_setting(self, key: str, option: Any) -> None:
        if key in self._preferences:
            options = self._preferences[key].get("options", [])
            if option in options:
                options.remove(option)
                self._persist_preferences()
                self.log(f"Option removed from {key}: {option}")

    ### SEARCH
    def search_preferences(self, keyword: str) -> Dict[str, Dict[str, Any]]:
        keyword = keyword.lower()
        return {
            k: v for k, v in self._preferences.items()
            if keyword in k.lower() or keyword in str(v.get("description", "")).lower()
        }

    ### IMPORT / EXPORT
    def export_profile(self, file_path: str, knowledgeBase=None, quizController=None) -> bool:
        try:
            profile = {
                "knowledgeBase": knowledgeBase.serialize() if knowledgeBase else {},
                "preferences": self._preferences,
                "userAuth": {}
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)

            self.log(f"Profile exported to {file_path}")
            return True

        except Exception as e:
            self.handle_error(e, "exporting profile")
            return False

    def import_profile(self, file_path: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                profile = json.load(f)

            self._preferences = profile.get("preferences", {})
            self._persist_preferences()

            self.log(f"Profile imported from {file_path}")
            return True

        except Exception as e:
            self.handle_error(e, "importing profile")
            return False

    ### SAVE TO DISK
    def _persist_preferences(self) -> None:
        try:
            with open(self._preferences_path, "w", encoding="utf-8") as f:
                json.dump(self._preferences, f, indent=2)
        except Exception as e:
            self.handle_error(e, "saving preferences")