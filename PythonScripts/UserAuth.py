import hashlib
import json
import os

class UserAuth:
    def __init__(self, user_file):
        # user_file is passed in from Controller, e.g. SaveData/user_data.json
        self.user_file = user_file
        os.makedirs(os.path.dirname(self.user_file), exist_ok=True)

    def __createUser(self, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump({"password_hash": password_hash}, f)

    def _verifyUser(self, password):
        try:
            with open(self.user_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return user_data["password_hash"] == password_hash
        except FileNotFoundError:
            return None

    def register(self, password):
        if os.path.exists(self.user_file):
            return False
        self.__createUser(password)
        return True
    
    def is_user_registered(self):
        return os.path.exists(self.user_file)
    