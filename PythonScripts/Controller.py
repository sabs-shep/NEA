import json
import os
import logging
import traceback
import importlib
import UserAuth
from pynput import keyboard
from CircularStack import CircularStack


class Controller:
    ### INITIALISATION
    def __init__(self, name: str):
        # Store raw name
        self.name = name
        
        with open("C:/temp/python_debug.txt", "a") as f:
            f.write(f"name={name}, type={type(name)}\n")
        # Debug: confirm type and value of name
        print(f"[Controller.__init__] name={repr(self.name)} type={type(self.name)}")
        # Create SaveData directory in AppData
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        base_dir = os.path.join(appdata, "NEAApp", "SaveData")
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

        # File paths
        self.log_file = os.path.join(base_dir, f"{self.name}_controller.log")
        self.global_shortcuts_file = os.path.join(base_dir, "controller_shortcuts.json")
        self.local_shortcuts_file = os.path.join(base_dir, f"{self.name}_shortcuts.json")
        self.user_data_file = os.path.join(base_dir, "user_data.json")

        # Login state
        self.__logged_in = False

        # Undo/redo stacks
        self._undo_CS = CircularStack()
        self._redo_CS = CircularStack()

        # Logger setup (hardened)
        try:
            safe_name = str(self.name) if self.name is not None else "Controller"
        except Exception:
            safe_name = "Controller"

        self.logger = logging.getLogger(safe_name)
        handler = logging.FileHandler(self.log_file, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Preferences
        self._preferences_path = os.path.join(base_dir, "settings.json")
        self._preferences: dict[str, dict] = {}

    ### LOGGING
    def log(self, message: str) -> None:
        self.logger.info(message)

    def handle_error(self, error: Exception, context: str = "") -> None:
        msg = f"Error {context}: {error}" if context else f"Error: {error}"
        self.logger.error(msg)
        self.logger.error(traceback.format_exc())

    ### PREFERENCES
    def load_preferences(self, filePath: str) -> bool:
        try:
            with open(filePath, "r", encoding="utf-8") as f:
                self._preferences = json.load(f)
            self._preferences_path = filePath
            self.log(f"Preferences loaded from {filePath}")
            return True
        except Exception as e:
            self.handle_error(e, "loading preferences")
            self._preferences = {}
            return False

    def get_preferences(self) -> dict[str, dict]:
        return self._preferences

    ### USER AUTHENTICATION
    def create_User(self, password) -> None:
        UA = UserAuth.UserAuth(self.user_data_file)
        result = UA.register(password)

        if not result:
            self.log("User creation failed: User already exists")
            return
        elif result:
            self.log("User created successfully")
            self.__logging_in(password)
        else:
            self.log("Unknown user creation error")

    def is_logged_in(self) -> bool:
        return self.__logged_in

    def __logging_in(self, password) -> None:
        UA = UserAuth.UserAuth(self.user_data_file)
        result = UA._verifyUser(password)

        if result is None:
            self.log("No user found during login attempt")
            return
        elif not result:
            self.log("Failed login attempt")
            return
        elif result:
            self.__logged_in = True
            self.log("User logged in")
        else:
            self.log("Unknown login error")

    def __logging_out(self) -> None:
        self.__logged_in = False
        self.log("User logged out")

    ### GETTERS
    def get_name(self) -> str: return self.name
    def get_log_file(self) -> str: return self.log_file
    def get_global_shortcuts_file(self) -> str: return self.global_shortcuts_file
    def get_local_shortcuts_file(self) -> str: return self.local_shortcuts_file
    
    ### SHORTCUT MANAGEMENT
    def _save_shortcut(self, file_path: str, keys, functs) -> None:
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    shortcuts = json.load(f)
            else:
                shortcuts = {}
        except Exception as e:
            self.handle_error(e, f"loading shortcuts from {file_path}")
            shortcuts = {}

        if isinstance(keys, (list, set, tuple)):
            key_id = "+".join(sorted(str(k) for k in keys))
        else:
            key_id = str(keys)

        shortcuts[key_id] = functs

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(shortcuts, f, indent=2)
            self.log(f"Shortcut saved: {key_id} -> {functs}")
        except Exception as e:
            self.handle_error(e, f"saving shortcut to {file_path}")

    def add_global_shortcut(self, keys, functs) -> None:
        self._save_shortcut(self.global_shortcuts_file, keys, functs)

    def add_local_shortcut(self, keys, functs) -> None:
        self._save_shortcut(self.local_shortcuts_file, keys, functs)

    def _load_shortcuts(self) -> dict:
        shortcuts = {}
        for file in [self.global_shortcuts_file, self.local_shortcuts_file]:
            try:
                if os.path.exists(file):
                    with open(file, "r", encoding="utf-8") as f:
                        shortcuts.update(json.load(f))
            except Exception as e:
                self.handle_error(e, f"loading shortcuts from {file}")
        return shortcuts

    ### SHORTCUT LISTENER
    def listen_shortcuts(self):
        shortcuts = self._load_shortcuts()
        pressed_keys = set()

        def on_press(key):
            try:
                pressed_keys.add(str(key))
                self.log(f"Key pressed: {key}")

                combo = "+".join(sorted(pressed_keys))
                if combo in shortcuts:
                    functs = shortcuts[combo]
                    self.log(f"Shortcut triggered: {combo} -> {functs}")

                    for func_name, module_name in functs:
                        try:
                            module = importlib.import_module(module_name)
                            func = getattr(module, func_name)
                            func()
                        except Exception as e:
                            self.handle_error(e, f"executing {func_name} from {module_name}")
            except Exception as e:
                self.handle_error(e, "on_press handler")

        def on_release(key):
            try:
                pressed_keys.discard(str(key))
                self.log(f"Key released: {key}")
            except Exception as e:
                self.handle_error(e, "on_release handler")

        self.log("Shortcut listener started")

        try:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            self.handle_error(e, "starting listener")

    ### UNDO / REDO ENGINE
    def push_undo(self, snapshot: dict) -> None:
        self._undo_CS.push(snapshot)
        self._redo_CS.clear()
        self.log("Undo snapshot pushed.")

    def undo(self) -> dict | None:
        snapshot = self._undo_CS.pop_new()
        if snapshot is None:
            self.log("Undo requested but stack is empty.")
            return None
        return snapshot

    def push_redo(self, snapshot: dict) -> None:
        self._redo_CS.push(snapshot)

    def redo(self) -> dict | None:
        snapshot = self._redo_CS.pop_new()
        if snapshot is None:
            self.log("Redo requested but stack is empty.")
            return None
        return snapshot

    def clear_history(self) -> None:
        self._undo_CS.clear()
        self._redo_CS.clear()
        self.log("Undo/redo history cleared.")