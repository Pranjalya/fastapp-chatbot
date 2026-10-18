import pytest
from app.auth.security import create_access_token, decode_access_token, verify_credentials

def test_verify_credentials():
    assert verify_credentials("kvothe", "password123") is True
    assert verify_credentials("admin", "admin123") is True
    assert verify_credentials("kvothe", "wrongpass") is False
    assert verify_credentials("nonexistent", "password123") is False

def test_jwt_token_lifecycle():
    username = "kvothe"
    token = create_access_token({"sub": username})
    assert isinstance(token, str)
    
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == username
