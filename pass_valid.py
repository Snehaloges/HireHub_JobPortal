import re
from passlib.hash import bcrypt
def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Valid password."
def hash_password(password:str) ->str:
    return bcrypt.hash(password)
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)
    