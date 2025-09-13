import jwt, datetime
from typing import Optional
from functools import wraps
from flask import request, jsonify

JWT_SECRET = "secret_key"

def create_jwt(user_id: int, role: str, hours_valid: int = 24) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int((datetime.datetime.utcnow() + datetime.timedelta(hours=hours_valid)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", None)
        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ")[1]
        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(payload, *args, **kwargs)  
    return wrapper
