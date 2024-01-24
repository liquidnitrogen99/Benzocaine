# tests/test_user_management.py

import pytest
import user_management as um

def test_add_user():
    assert um.add_user("test_user", "test@example.com") == "User added"
    assert um.add_user("test_user", "test@example.com") == "User already exists"

def test_get_user():
    assert um.get_user("test_user") == {"username": "test_user", "email": "test@example.com"}
    assert um.get_user("nonexistent_user") == "User not found"

def test_delete_user():
    assert um.delete_user("test_user") == "User deleted"
    assert um.delete_user("test_user") == "User not found"
