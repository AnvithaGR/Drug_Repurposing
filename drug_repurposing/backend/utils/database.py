import json
import os
from typing import Optional, Dict
from backend.utils.security import get_password_hash, verify_password

USERS_FILE = "data/users.json"


class UserDatabase:
    """Simple JSON-based user database. Can be replaced with SQLAlchemy later."""
    
    def __init__(self):
        self.users_file = USERS_FILE
        self._ensure_file_exists()
        self._init_default_user()

    def _ensure_file_exists(self):
        """Create users.json file if it doesn't exist."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w") as f:
                json.dump({"users": []}, f, indent=2)

    def _init_default_user(self):
        """Initialize with a default admin user if no users exist."""
        data = self._read_file()
        if not data.get("users"):
            default_user = {
                "id": 1,
                "username": "admin",
                "email": "admin@drug-repurposing.com",
                "password_hash": get_password_hash("Admin@123456"),
                "is_active": True,
                "email_verified": True
            }
            data["users"].append(default_user)
            self._write_file(data)

    def _read_file(self) -> Dict:
        """Read users from JSON file."""
        with open(self.users_file, "r") as f:
            return json.load(f)

    def _write_file(self, data: Dict):
        """Write users to JSON file."""
        with open(self.users_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        data = self._read_file()
        for user in data.get("users", []):
            if user["username"] == username:
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        data = self._read_file()
        for user in data.get("users", []):
            if user["email"].lower() == email.lower():
                return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        data = self._read_file()
        for user in data.get("users", []):
            if user["id"] == user_id:
                return user
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        if not user.get("is_active", True):
            return None
        # Check if email is verified for login
        if not user.get("email_verified", False):
            return None
        return user

    def create_user(self, username: str, email: str, password: str) -> Dict:
        """Create a new user."""
        # Check if user already exists
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        
        if self.get_user_by_email(email):
            raise ValueError(f"Email '{email}' is already registered")
        
        data = self._read_file()
        new_id = max([u["id"] for u in data.get("users", [])], default=0) + 1
        
        new_user = {
            "id": new_id,
            "username": username,
            "email": email,
            "password_hash": get_password_hash(password),
            "is_active": True,
            "email_verified": False
        }
        data["users"].append(new_user)
        self._write_file(data)
        
        # Return user without password hash
        return {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "is_active": new_user["is_active"],
            "email_verified": new_user["email_verified"]
        }

    def verify_user_email(self, email: str) -> bool:
        """Mark user's email as verified."""
        data = self._read_file()
        for user in data.get("users", []):
            if user["email"].lower() == email.lower():
                user["email_verified"] = True
                self._write_file(data)
                return True
        return False

    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        data = self._read_file()
        original_length = len(data.get("users", []))
        data["users"] = [u for u in data.get("users", []) if u["username"] != username]
        
        if len(data["users"]) < original_length:
            self._write_file(data)
            return True
        return False


# Global instance
user_db = UserDatabase()
